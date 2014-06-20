create table users(
	username varchar(32) not null primary key,
    password varchar(124) not null,
    enabled smallint not null
    );

 create table authorities (
 	username varchar(32) not null,
    authority varchar(50) not null,
    constraint fk_authorities_users foreign key(username) references users(username));
    create unique index ix_auth_username on authorities (username,authority);

create table groups (
	id bigint NOT NULL AUTO_INCREMENT primary key, 
	group_name varchar(50) not null);

create table group_authorities (
	group_id bigint not null, 
	authority varchar(50) not null, 
	constraint fk_group_authorities_group foreign key(group_id) references groups(id));

create table group_members (
	id bigint NOT NULL AUTO_INCREMENT primary key, 
	username varchar(32) not null, 
	group_id bigint not null, 
	constraint fk_group_members_group foreign key(group_id) references groups(id));
	
CREATE TABLE `acl_class` (
  `ID` bigint(20) NOT NULL auto_increment,
  `CLASS` varchar(100) NOT NULL,
  PRIMARY KEY  (`ID`),
  UNIQUE KEY `UNIQUE_UK_2` (`CLASS`)
  )AUTO_INCREMENT=1;
  
CREATE TABLE `acl_entry` (
  `ID` bigint(20) NOT NULL auto_increment,
  `ACL_OBJECT_IDENTITY` bigint(20) NOT NULL,
  `ACE_ORDER` int(11) NOT NULL,
  `SID` bigint(20) NOT NULL,
  `MASK` int(11) NOT NULL,
  `GRANTING` tinyint(1) NOT NULL,
  `AUDIT_SUCCESS` tinyint(1) NOT NULL,
  `AUDIT_FAILURE` tinyint(1) NOT NULL,
  PRIMARY KEY  (`ID`),
  UNIQUE KEY `UNIQUE_UK_4` (`ACL_OBJECT_IDENTITY`,`ACE_ORDER`),
  KEY `SID` (`SID`)
  )AUTO_INCREMENT=1;
  
CREATE TABLE `acl_object_identity` (
  `ID` bigint(20) NOT NULL auto_increment,
  `OBJECT_ID_CLASS` bigint(20) NOT NULL,
  `OBJECT_ID_IDENTITY` bigint(20) NOT NULL,
  `PARENT_OBJECT` bigint(20) default NULL,
  `OWNER_SID` bigint(20) default NULL,
  `ENTRIES_INHERITING` tinyint(1) NOT NULL,
  PRIMARY KEY  (`ID`),
  UNIQUE KEY `UNIQUE_UK_3` (`OBJECT_ID_CLASS`,`OBJECT_ID_IDENTITY`),
  KEY `OWNER_SID` (`OWNER_SID`),
  KEY `PARENT_OBJECT` (`PARENT_OBJECT`)
)AUTO_INCREMENT=1;

CREATE TABLE `acl_sid` (
  `ID` bigint(20) NOT NULL auto_increment,
  `PRINCIPAL` tinyint(1) NOT NULL,
  `SID` varchar(100) NOT NULL,
  PRIMARY KEY  (`ID`),
  UNIQUE KEY `UNIQUE_UK_1` (`PRINCIPAL`,`SID`)
) ;
