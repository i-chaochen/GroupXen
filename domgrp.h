/******************************************************************************
 * 	
 * 	domgrp.h
 * 	Generic domain group-handling functions
 *
 ****************************************************************************/

#ifndef __XEN_DOM_GROUP_H__
#define __XEN_DOM_GROUP_H__

#include <public/domgrpctl.h>

extern	struct	list_head  domgrplist;

void	get_grp_info(struct  domain_group  *grp, xen_domgrpctl_getgrpinfo_t * info);

struct	domain_group  *find_grp_by_id(dgid_t  dgid);

uint16_t   get_new_group_id(void);

struct	domain_group	*domain_group_create(dgid_t  dgid);

/******************************************************************************
 * 	
 * 	delete domain group
 *
 ****************************************************************************/
int del_dom_from_grp(struct domain *old_dom);

/******************************************************************************
 * 	
 * 	add domain group
 *
 ****************************************************************************/
int add_dom_to_grp(struct domain *dom, dgid_t dgid);


/******************************************************************************
 * 	
 * 	pause domain group
 *
 ****************************************************************************/
int pause_grp(dgid_t dgid);

/******************************************************************************
 * 	
 * 	unpause domain group
 *
 ****************************************************************************/
int unpause_grp(dgid_t dgid);

/******************************************************************************
 * 	
 * 	destroy domain group
 *
 ****************************************************************************/
int domain_group_destroy(dgid_t dgid);

/******************************************************************************
 * 	
 * 	init domain group
 *
 ****************************************************************************/
int init_domain_groups(void);

#endif                         /* __XEN_DOM_GROUP_H__ */

