##########################################################
#							                             #	
#	XendDomainGroupInfo accepts data from xc.c	         #
#							                             #
##########################################################

import logging
import string
import sxp
import uuid
import xen.lowlevel.xc
import XendDomain
import XendDomainInfo
from xen.xend.XendError import VmError
from xen.xend.xenstore.xstransact import xstransact
from xen.xend.XendConstants import XS_GRPROOT


xc = xen.lowlevel.xc.xc()
log = logging.getLogger("xend.XendDomainGroupInfo")
default_ops = ['create','shutdown','pause','unpause','save','restore',
               'migrate_up','migrate_down']

######################################	
#	 create domain group 			 #
######################################
def create(config):
    """Creates and start a VM using the supplied configuration. 

    """
    log.debug("XendDomainGroupInfo.create(%s)", config)

    grp = XendDomainGroupInfo(parseConfig(config))

    try:
        grp.construct()
        return grp 
    except:
        raise VmError('Domain group construction failed')

##################################	
#	recreate domain group 		 #
##################################
def recreate(xeninfo):
    """Create the VM object for an existing domain group.  The domain group must not
    be dying, as the paths in the store should already have been removed,
    and asking us to recreate them causes problems.

    """
    log.debug("XendDomainGroupInfo.recreate(%s)", xeninfo)

    dgid = xeninfo['dgid']
    dg_handle = xeninfo['dg_handle']
    xeninfo['dguuid'] = uuid.toString(dg_handle)

    log.info("Recreating domain group %d, UUID %s.", dgid, xeninfo['dguuid'])

    return XendDomainGroupInfo(xeninfo)

#######################################	
#	parse domain group config	      #
#######################################
def parseConfig(config):
    result = {}

    result['grp_name'] = sxp.child_value(config,'grp_name')
    result['member_list'] = sxp.child_value(config,'member_list')

    log.info("parseConfig result is %s" % result)
    return result

##################################	
#	     get group id		     #
##################################
def grp_get(dgid):
    try:
        grplist = xc.domain_group_getinfo(dgid, 1)
        if grplist and grplist[0]['dgid'] == dgid:
            return grplist[0]
    except Exception, err:
        # ignore missing domain group
        log.debug("grp_getinfo(%d) failed, ignoring: %s", dgid, str(err))
    return None


###############################################
#							                  #	
#		Xend Domain_Group info	              #
#							                  #
###############################################
class XendDomainGroupInfo:
    """An object represents a domain group. 

    """
    def __init__(self, info):

       self.info = info

        if self.infoIsSet('dgid'):
            self.dgid = self.info['dgid']

        if not self.infoIsSet('dguuid'):
            self.info['dguuid'] = uuid.toString(uuid.create())
        self.dguuid = self.info['dguuid']

        if not self.infoIsSet('grp_name'):
            self.info['grp_name'] = ("Group-%s" % self.dguuid)
        self.grp_name = self.info['grp_name']

        if not self.infoIsSet('grp_path'):
            self.info['grp_path'] = "%s%s" % (XS_GRPROOT,self.dguuid)
        self.grppath = self.info['grp_path']

        self.parse_member_list()
        self.validateInfo()

##############################
#							 #	
#		parse member list	 #
#							 #
##############################
    def parse_member_list(self):
        # set up member info dict to pair members and their manifests
        # TODO: add checks to ensure neither component is empty
        self.members = []
        self.member_info = {}

        if self.infoIsSet('member_list'):
            for str in self.info['member_list']:
                if (':' not in str):
                    raise VmError('invalid grpinfo format; member_list missing \':\'')
                smember = str.split(':')
                mbr_name = smember[0]
                self.members.append(mbr_name)
                mbr_manifest_path = smember[1]
                self.member_info[mbr_name] = mbr_manifest_path

        self.size = len(self.member_info)
        self.info['size'] = self.size

######################################
#		get group name				 #
######################################
    def getName(self):
        return self.info['grp_name']

######################################	
#		get group id				 #
###################################### 
    def getDgid(self):
        return self.info['dgid']


#####################################	
#		get group uuid			    #
#####################################    
    def getDguuid(self):
        return self.info['dguuid']

######################################	
#		update group 				 #
######################################
    def update(self, info = None):
        log.trace("XendDomainGroupInfo.update(%s) on grp %d", self.dgid)

        if not info:
            xdg = xen.xend.XendDomainGroup.instance()
            info = xdg.grp_lookup(self.dgid)
            if not info:
                return
            
        self.info.update(info)
        self.dgid = self.info['dgid']
        self.dguuid = self.info['dguuid']
        self.grp_name = self.info['grp_name']
        self.parse_member_list()
        self.validateInfo()

        log.trace("XendDomainGroupInfo.update done on grp %d: %s", self.dgid, 
                  self.info)


    def sxpr(self):
        return self.info


    def validateInfo(self):
        def defaultInfo(name, val):
            if not self.infoIsSet(name):
                self.info[name] = val()
        try:
            defaultInfo('grp_name', lambda: "Group-%s" % self.dguuid)
            self.check_name(self.info['grp_name'])
        except KeyError, exn:
            log.exception(exn)
            raise VmError('Unspecified domain group detail: %s' % exn)

    def _readGrp(self, *args):
        return xstransact.Read(self.grppath, *args)


    def _writeGrp(self, *args):
        return xstransact.Write(self.grppath, *args)


    def _removeGrp(self, *args):
        return xstransact.Remove(self.grppath, *args)


    def storeGrpDetails(self):
        to_store = { 
                     'dgid': str(self.dgid),
                     'dguuid': self.dguuid,
                     'grp_name': self.grp_name,
                     'members': ", ".join(self.members)
                   }
        self._writeGrp(to_store)


    # create an empty group
    def construct(self, dguuid = None):
       if dguuid:
            dg_handle = uuid.fromString(dguuid)
        else:
            dg_handle = uuid.fromString(self.info['dguuid'])
        self.dgid = xc.domain_group_create(dg_handle)
        if (self.dgid < 0) or (self.dgid == None):
            raise VmError('Creating domain group %s failed' % self.info['grp_name'])
        self.info['dgid'] = self.dgid
        self.storeGrpDetails()


    def infoIsSet(self, name):
        return name in self.info and self.info[name] is not None


    def check_name(self, name):
        # check for lack of name
        if name is None or name == '':
            raise VmError('missing grp name')
        # check name for invalid characters
        for c in name:
            if c in string.digits: continue
            if c in '_-.:/+': continue
            if c in string.ascii_letters: continue
            raise VmError("check_name: invalid grp name caused by [%s]" % c)
        # check for duplicate names
        xdg = xen.xend.XendDomainGroup.instance()
        grp = xdg.grp_lookup_nr(name)
        if grp and grp.info['dguuid'] != self.info['dguuid']:
            raise VmError("Group name %s already exists" % name)


    def destroy(self, rmxs):
        ret = xc.domain_group_destroy(self.dgid)
        if ret == 0 and rmxs:
            self._removeGrp()
        return ret
            

    def pause(self):
        xc.domain_group_pause(self.dgid)


    def unpause(self):
        xc.domain_group_unpause(self.dgid)
        