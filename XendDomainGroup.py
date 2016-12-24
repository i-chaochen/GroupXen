######################################################################################################
#
#
#		Xend_Domain_Group
#
#
######################################################################################################

import logging
import os
import socket
import sys
import threading
import uuid

import xen.lowlevel.xc
from xen.xend import XendDomain
from xen.xend import XendDomainGroupInfo
from xen.xend.XendError import XendError
from XendLogging import log
from xen.xend.XendConstants import XS_GRPROOT, GROUP0_ID, \
     GROUP0_NAME, NULL_GROUP_ID, NULL_GROUP_NAME


xc = xen.lowlevel.xc.xc()


class XendDomainGroup:

    def __init__(self):
        self.domain_groups = {}
        self.domain_groups_lock = threading.RLock()
        self.xd = XendDomain.instance()
        self.xst = xen.xend.xenstore.xstransact.xstransact

##########################################################
#		init domain group 			 #
##########################################################
    def init(self):
        
        #xstransact.Mkdir(XS_GRPROOT)
        #xstransact.SetPermissions(XS_GRPROOT, {'dom': DOM0_ID})

        self.domain_groups_lock.acquire()
        try:
            grps = self.xen_domain_groups()
            for dgid,grpdata in grps.items():
                log.debug("init'ing grp%s: %s", dgid, grpdata)
                if dgid == GROUP0_ID:
                    grpdata['grp_name'] = GROUP0_NAME
                elif dgid == NULL_GROUP_ID: 
                    grpdata['grp_name'] = NULL_GROUP_NAME
                else:
                    path = "%s%s/grp_name" % (XS_GRPROOT,grpdata['dguuid'])
                    grpdata['grp_name'] = self.xst.Read(path)
                    if not grpdata['grp_name']:
                        grpdata['grp_name'] = "Group-%s" % grpdata['dguuid']
                grpinfo = XendDomainGroupInfo.recreate(grpdata)
                self._add_domain_group(grpinfo)
                grpinfo.storeGrpDetails()
        finally:
            self.domain_groups_lock.release()

##########################################################
#		add domain group 			 #
##########################################################
    def _add_domain_group(self, info):
        dgid = info.dgid
        self.domain_groups[dgid] = info
        log.debug("Added grp%s to domain_groups: %s", dgid, info)


##########################################################
#		delete domain group 			 #
##########################################################
    def _delete_domain_group(self, dgid):
        info = self.domain_groups.get(dgid)
        if info:
            del self.domain_groups[dgid]
        log.debug("Deleted grp%s from domain_groups", dgid)


##########################################################
#		pre-pending group path			 #
##########################################################
    def _prependGrpPath(self, dguuid, string):
        grppath = "%s%s" % (XS_GRPROOT,dguuid)
        return "%s%s" % (grppath,string)


##########################################################
#		get group name				 #
##########################################################
    def _getGrpName(self, dguuid):
        name = ""
        namepath = ""
        try:
            namepath = self._prependGrpPath(dguuid, "/grp_name")
            name = self.xst.Read(namepath)
        except:
            log.exception("Error reading %s from xenstore", namepath)
        if (name == "") or (name == None):
            grpinfo = self.grp_lookup_nr(dguuid)
            if grpinfo:
                name = grpinfo.grp_name
            else:
                name = "Group-%s" % dguuid
        return name


##########################################################
#		rebuild group config data		 #
##########################################################
    def _rebuild_config(self, grpdata):
        domlist = []
        for domid in grpdata['member_list']:
            dominfo = self.xd.domain_lookup_nr(domid)
            if dominfo:
                domname = dominfo.getName()
                # TODO: could store/retrieve member config paths to/from xs, 
                # but at the moment there is no need for accurate values once
                # the members are started
                domlist.append(domname+":nullconfig")

        sxpr = {}
        sxpr['dgid'] = grpdata['dgid']
        sxpr['dg_handle'] = grpdata['dg_handle']
        sxpr['dguuid'] = uuid.toString(grpdata['dg_handle'])
        sxpr['grp_name'] = self._getGrpName(sxpr['dguuid'])
        sxpr['member_list'] = domlist
        sxpr['size'] = len(domlist)
        
        return sxpr


##########################################################
#		xen domain group			 #
##########################################################
    def xen_domain_groups(self):
        grps = {}
        grplist = xc.domain_group_getinfo()
        for grp in grplist:
            dgid = grp['dgid']
            grpdata = self._rebuild_config(grp)
            grps[dgid] = grpdata
        return grps


##########################################################
#		refresh	group				 #
##########################################################
    def refresh(self):
        grps = self.xen_domain_groups()

        for grp in self.domain_groups.values():
            info = grps.get(grp.dgid)
            if info:
                grp.update(info)
            else:
                self._delete_domain_group(grp.dgid)

        for grp in grps:
            if grp not in self.domain_groups:
                try:
                    grpinfo = XendDomainGroupInfo.recreate(grps[grp])
                    self._add_domain_group(grpinfo)
                except:
                    log.exception(
                        "Failed to recreate information for domain "
                        "group %d.", grp)

       self.push_grp_data_to_xenstore()

##########################################################
#		push group data to xenstore		 #
##########################################################
    def push_grp_data_to_xenstore(self):
        for grpinfo in self.domain_groups.values():
            grpinfo.storeGrpDetails()


##########################################################
#		group lookup name, id, dguuid		 #
##########################################################
    def grp_lookup_nr(self, grp):
        self.domain_groups_lock.acquire()
        try:
            # match by name
            for grpinfo in self.domain_groups.values():
                if grpinfo.getName() == grp:
                    return grpinfo
            # match by id
            try:
                if int(grp) in self.domain_groups:
                    return self.domain_groups[int(grp)]
            except ValueError:
                pass
            # match by dguuid
            for grpinfo in self.domain_groups.values():
                if grpinfo.getDguuid() == grp:
                    return grpinfo
            # group not found
            return None
        finally:
            self.domain_groups_lock.release()


##########################################################
#		group lookup				 #
##########################################################
    def grp_lookup(self, grp):
        self.domain_groups_lock.acquire()
        try:
            self.refresh()
            return self.grp_lookup_nr(grp)
        finally:
            self.domain_groups_lock.release()


##########################################################
#		group members info			 #
##########################################################
    def grp_members(self, dgid):
        grpinfo = self.grp_lookup(dgid)
       return grpinfo.members

##########################################################
#		group list				 #
##########################################################
    def grp_list(self):
        self.domain_groups_lock.acquire()
        try:
            self.refresh()
            return self.domain_groups.values()
        finally:
            self.domain_groups_lock.release()

##########################################################
#		group create				 #
##########################################################
    def grp_create(self, config):
        self.domain_groups_lock.acquire()
        try:
            grpinfo = XendDomainGroupInfo.create(config)
            self._add_domain_group(grpinfo)
            return grpinfo
        finally:
            self.domain_groups_lock.release()

##########################################################
#		group shutdown				 #
##########################################################
    def grp_shutdown(self, dgid, reason):
        members = self.grp_members(dgid)
        for domname in members:
            dominfo = self.xd.domain_lookup(domname)
            dominfo.shutdown(reason)

##########################################################
#		group destroy				 #
##########################################################
    def grp_destroy(self, dgid, rmxs = True):
        ret = -1
        self.domain_groups_lock.acquire()
        try:
            grpinfo = self.grp_lookup(dgid)
            ret = grpinfo.destroy(rmxs)
            if ret == 0:
                self._delete_domain_group(dgid)
        finally:
            self.domain_groups_lock.release()
            return ret

##########################################################
#		group save				 #
##########################################################
    def grp_save(self, dgid, prefix):
        members = self.grp_members(dgid)
        for dom in members:
            self.xd.domain_save(dom, prefix + "." + dom)
        self.grp_destroy(dgid)

##########################################################
#		group restore				 #
##########################################################
    def grp_restore(self, srcs):
        for dompath in srcs:
            self.xd.domain_restore(dompath, paused=False)

##########################################################
#		group suspend				 #
##########################################################
    def grp_suspend(self, dgid):
        log.debug("grp_suspend is not working yet")
    #    members = self.grp_members(dgid)
    #    for dom in members:
    #        self.xd.domain_suspend(dom)
    #    self.grp_destroy(dgid, rmxs=False)

##########################################################
#		group resemue				 #
##########################################################
    def grp_resume(self, dgid):
        log.debug("grp_resume is not working yet")
    #    member_list_str = self.xst.Read(XS_GRPROOT, "%s/members" % dguuid)
    #    member_list = member_list_str.split(", ")
    #    for dom in member_list:
    #        self.xd.domain_resume(dom)

##########################################################
#		group pasuse				 #
##########################################################
    def grp_pause(self, dgid):
        self.domain_groups_lock.acquire()
        try:
            grpinfo = self.grp_lookup(dgid)
            return grpinfo.pause()
        finally:
            self.domain_groups_lock.release()

##########################################################
#		group unpasuse				 #
##########################################################
    def grp_unpause(self, dgid):
        self.domain_groups_lock.acquire()
        try:
            grpinfo = self.grp_lookup(dgid)
            return grpinfo.unpause()
        finally:
            self.domain_groups_lock.release()

##########################################################
#		group join				 #
##########################################################
    def grp_join(self, domid, dgid):
        self.domain_groups_lock.acquire()
        try:
            dominfo = self.xd.domain_lookup(domid)
            old_dgid = dominfo.getDgid()
            rc = xc.domain_group_join(domid, dgid)
            if rc != 0:
                raise XendError("group_join failed with error: %s" % rc)
            dominfo = self.xd.domain_lookup(domid)
            dominfo._storeVmDetails()
            dominfo._storeDomDetails()
            self.xd.managed_config_save(dominfo)
            grpinfo = self.grp_lookup(dgid)
            grpinfo.storeGrpDetails()
            old_grpinfo = self.grp_lookup(old_dgid)
            old_grpinfo.storeGrpDetails()
            log.debug("dom%s joining grp%s", domid, dgid)
            return rc
        finally:
            self.domain_groups_lock.release()

##########################################################
#		group migrate				 #
##########################################################
    def grp_migrate(self, dgid, dst, live, resource, port):

       def threadHelper(dom):
            return threading.Thread(target = self.xd.domain_migrate, 
                                    args = (dom,dst,live,resource,port))

        try:
            member_names = self.grp_members(dgid)
            migration_threads = {}
            # spawn and start a threaded migration request
            # for each group member
            for domname in member_names:
                migration_threads[domname] = threadHelper(domname)
                migration_threads[domname].start()
                log.debug("Migration began for domain %s to %s",
                           domname, dst)
            # block until all group members finish migration
            for domname in member_names:
                migration_threads[domname].join()
                log.debug("Migration complete for domain %s to %s", 
                           domname, dst)
            self.grp_destroy(dgid)
        except e:
            log.exception("error during grp_migrate: %s", str(e))
            self.domain_groups_lock.release()

##########################################################
#		init constructor			 #
##########################################################
def instance():
    """Singleton constructor. Use this instead of the class constructor.
    """
    global inst
    try:
        inst
    except:
        inst = XendDomainGroup()
        inst.init()
    return inst
