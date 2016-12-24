/******************************************************************************
*
*	Generic group management operations via node control stack.
*
******************************************************************************/

#ifndef __XEN_PUBLIC_DOMGRPCTL_H__
#define __XEN_PUBLIC_DOMGRPCTL_H__

#if !defined(__XEN__) && !defined(__XEN_TOOLS__)

#error "domgrpctl operations are intended for use by node control tools only"
#endif

#include "xen.h"

#define XEN_DOMGRPCTL_INTERFACE_VERSION 0x00000001

#define MAX_GROUP_SIZE                 24
#define NULL_GROUP_ID                  (0x7FFFU)
#define INVAL_GROUP_ID                 (0xFFFFU)

#define XEN_DOMGRPCTL_creategrp                1

struct	xen_domgrpctl_creategrp{
	dgid_t	dgid;
	xen_domain_group_handle_t  handle;
};
typedef	struct xen_domgrpctl_creategrp	xen_domgrpctl_creategrp_t;

DEFINE_XEN_GUEST_HANDLE(xen_domgrpctl_creategrp_t);

#define	XEN_DOMGRPCTL_joingrp		2

struct xen_domgrpctl_joingrp{
	domid_t	   domid;
	dgid_t	   dgid;
};

typedef struct xen_domgrpctl_joingrp xen_domgrpctl_joingrp_t;
DEFINE_XEN_GUEST_HANDLE(xen_domgrpctl_joingrp_t);

#define XEN_DOMGRPCTL_pausegrp         3
struct xen_domgrpctl_pausegrp {
       dgid_t dgid;
};
typedef struct xen_domgrpctl_pausegrp xen_domgrpctl_pausegrp_t;
DEFINE_XEN_GUEST_HANDLE(xen_domgrpctl_pausegrp_t);

#define XEN_DOMGRPCTL_unpausegrp       4
struct xen_domgrpctl_unpausegrp {
       dgid_t dgid;
};
typedef struct xen_domgrpctl_unpausegrp xen_domgrpctl_unpausegrp_t;
DEFINE_XEN_GUEST_HANDLE(xen_domgrpctl_unpausegrp_t);

#define XEN_DOMGRPCTL_destroygrp       5
struct xen_domgrpctl_destroygrp {
       dgid_t dgid;
};
typedef struct xen_domgrpctl_destroygrp xen_domgrpctl_destroygrp_t;
DEFINE_XEN_GUEST_HANDLE(xen_domgrpctl_destroygrp_t);

#define XEN_DOMGRPCTL_getgrpinfo       6
struct xen_domgrpctl_getgrpinfo {
       dgid_t dgid;
       uint16_t size;
       domid_t member_list[MAX_GROUP_SIZE];
       xen_domain_group_handle_t handle;
};
typedef struct xen_domgrpctl_getgrpinfo xen_domgrpctl_getgrpinfo_t;
DEFINE_XEN_GUEST_HANDLE(xen_domgrpctl_getgrpinfo_t);


/******************************************************************************
 * 	
 * 	 domain group control struct "u"
 *
 ****************************************************************************/
struct xen_domgrpctl {
       uint32_t cmd;
       uint32_t interface_version;
       union {
               struct xen_domgrpctl_creategrp create_grp;
               struct xen_domgrpctl_joingrp join_grp;
               struct xen_domgrpctl_pausegrp pause_grp;
               struct xen_domgrpctl_unpausegrp unpause_grp;
               struct xen_domgrpctl_destroygrp destroy_grp;
               struct xen_domgrpctl_getgrpinfo get_grp_info;
       }u;
};
typedef struct xen_domgrpctl xen_domgrpctl_t;
DEFINE_XEN_GUEST_HANDLE(xen_domgrpctl_t);

#endif /*__XEN_PUBLIC_DOMGRPCTL_H__*/
