create table cluster_info (
	id bigint NOT NULL AUTO_INCREMENT, 
	name varchar(255),
        init bigint default 0, 
	primary key (id));

create unique index ix_cluster_name on cluster_info (name);
	
create table server_info (
	id bigint  NOT NULL AUTO_INCREMENT, 
	name varchar(255),
	cluster_id bigint,
	primary key (id));

create table task_info (
        id bigint  NOT NULL AUTO_INCREMENT,
        description varchar(255),
        reference  varchar(255),
        operation_id bigint,
        cluster_name varchar(255),
        primary key (id));

create table operation_info (
        id bigint  NOT NULL AUTO_INCREMENT,
        operation_type varchar(255),
        commitSupported varchar(255),
        pauseSupported varchar(255),
        stopSupported  varchar(255),
        percentageSupported varchar(255),
        primary key (id));

create table volume_info (
        id bigint  NOT NULL AUTO_INCREMENT,
        name varchar(255),
        cluster_id varchar(255),
        primary key(id));

insert into cluster_info(name) values("StorCluster");
alter table task_info add constraint FK_CLUSTER_ID foreign key (operation_id) references opration_info(id);
insert into operation_info(id, operation_type,commitSupported,pauseSupported,stopSupported,percentageSupported) values ('1','DISK_FORMAT','true','true','true','true');
insert into operation_info(id, operation_type,commitSupported,pauseSupported,stopSupported,percentageSupported) values ('2','BRICK_MIGRATE','true','true','true','true');
insert into operation_info(id, operation_type,commitSupported,pauseSupported,stopSupported,percentageSupported) values ('3','VOLUME_REBALANCE','true','true','true','true');
create unique index ix_cluster_server on server_info (name, cluster_id);
alter table server_info add constraint FK_CLUSTER_ID foreign key (cluster_id) references cluster_info(id);
