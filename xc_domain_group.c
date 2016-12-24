/******************************************************************************
 * xc_domain_group.c
 * 
 * API for manipulating and obtaining information on domain groups.
 * 
 ******************************************************************************/

#include "xc_private.h"
#include <xen/memory.h>


/******************************************************************************
 * 
 *	domain group create
 * 
 ******************************************************************************/
int xc_domain_group_create(int xc_handle, 
                          xen_domain_group_handle_t handle,
                          uint32_t *pdgid)
{
       int err;
       DECLARE_DOMGRPCTL;
       domgrpctl.cmd = XEN_DOMGRPCTL_creategrp;
       memcpy(domgrpctl.u.create_grp.handle, handle,
              sizeof(xen_domain_group_handle_t));
       
       err = do_domgrpctl(xc_handle, &domgrpctl);
       if (err) 
               return err;

       *pdgid = (uint16_t)domgrpctl.u.get_grp_info.dgid;
       return 0;
}

/******************************************************************************
 * 
 *	domain group pause
 * 
 ******************************************************************************/
int xc_domain_group_pause(int xc_handle, uint32_t dgid)
{
       DECLARE_DOMGRPCTL;
       domgrpctl.cmd = XEN_DOMGRPCTL_pausegrp;
       domgrpctl.u.pause_grp.dgid = (dgid_t) dgid;
       return do_domgrpctl(xc_handle, &domgrpctl);
}

/******************************************************************************
 * 
 *	domain group unpause
 * 
 ******************************************************************************/
int xc_domain_group_unpause(int xc_handle, uint32_t dgid)
{
       DECLARE_DOMGRPCTL;
       domgrpctl.cmd = XEN_DOMGRPCTL_unpausegrp;
       domgrpctl.u.unpause_grp.dgid = (dgid_t) dgid;
       return do_domgrpctl(xc_handle, &domgrpctl);
}

/******************************************************************************
 * 
 *	domain group destroy
 * 
 ******************************************************************************/
int xc_domain_group_destroy(int xc_handle, uint32_t dgid)
{
       DECLARE_DOMGRPCTL;
       domgrpctl.cmd = XEN_DOMGRPCTL_destroygrp;
       domgrpctl.u.destroy_grp.dgid = (dgid_t) dgid;
       return do_domgrpctl(xc_handle, &domgrpctl);
}

/******************************************************************************
 * 
 *	domain group join
 * 
 ******************************************************************************/
int xc_domain_group_join(int xc_handle, uint32_t domid, uint32_t dgid)
{
       DECLARE_DOMGRPCTL;
       domgrpctl.cmd = XEN_DOMGRPCTL_joingrp;
       domgrpctl.u.join_grp.domid = (domid_t) domid;
       domgrpctl.u.join_grp.dgid = (dgid_t) dgid;
       return do_domgrpctl(xc_handle, &domgrpctl);
}

#define TRANSFER_LIST_TO_INFO(list_name)                               \
       memcpy(info->list_name, domgrpctl.u.get_grp_info.list_name,     \
               MAX_GROUP_SIZE*sizeof(domid_t));

/******************************************************************************
 * 
 *	 domain group getinfo
 * 
 ******************************************************************************/
int xc_domain_group_getinfo(int xc_handle, uint32_t first_dgid,
                           unsigned int max_grps, xc_grpinfo_t * info)
{
       unsigned int nr_grps;
       uint32_t next_dgid = first_dgid;
       DECLARE_DOMGRPCTL;
       int rc = 0;

       memset(info, 0, max_grps * sizeof(xc_grpinfo_t));

       for (nr_grps = 0; nr_grps < max_grps; nr_grps++) {
               domgrpctl.cmd = XEN_DOMGRPCTL_getgrpinfo;
               domgrpctl.u.get_grp_info.dgid = (dgid_t) next_dgid;

               rc = do_domgrpctl(xc_handle, &domgrpctl);
               if (rc < 0)
                       break;

               info->dgid = (uint16_t) domgrpctl.u.get_grp_info.dgid;
               info->size = (uint16_t) domgrpctl.u.get_grp_info.size;

               TRANSFER_LIST_TO_INFO(member_list);
               memcpy(info->handle, domgrpctl.u.get_grp_info.handle,
                      sizeof(xen_domain_group_handle_t));

               next_dgid = (uint16_t) domgrpctl.u.get_grp_info.dgid + 1;
               info++;
       }

       if (!nr_grps)
               return rc;

       return nr_grps;
}
