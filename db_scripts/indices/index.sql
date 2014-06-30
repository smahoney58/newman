
DELIMITER $$

drop procedure if exists drop_index_if_exists $$
create procedure drop_index_if_exists(in thetable varchar(128), in theindexname varchar(128) )
begin
 if((select count(*) as index_exists from information_schema.statistics where table_schema = database() and table_name =
thetable and index_name = theindexname) > 0) then
   set @s = concat('drop index ' , theindexname , ' on ' , thetable);
   prepare stmt from @s;
   execute stmt;
 end if;
end $$

delimiter ;


call drop_index_if_exists('facts', 'idx_facts_subject');
call drop_index_if_exists('facts', 'idx_facts_schema');
call drop_index_if_exists('facts', 'idx_facts_schema_pred');
call drop_index_if_exists('facts', 'idx_facts_pred');
call drop_index_if_exists('facts', 'idx_facts_obj');
call drop_index_if_exists('facts', 'idx_facts_tx');

call drop_index_if_exists('email', 'idx_email_id');

call drop_index_if_exists('large_text', 'idx_text_subject');
call drop_index_if_exists('large_text', 'idx_text_sha');
call drop_index_if_exists('large_text', 'idx_text_tx');

create index idx_facts_subject on facts (subject(1000));
create index idx_facts_schema on facts(schema_name);
create index idx_facts_schema_pred on facts(schema_name, predicate);
create index idx_facts_pred on facts(predicate);
create index idx_facts_obj on facts(obj(8192));
create index idx_facts_tx on facts(tx);

create index idx_email_id on email(id);
create index idx_text_subject on large_text(subject);
create index idx_text_sha on large_text(sha512);
create index idx_text_tx on large_text(tx);


drop procedure if exists drop_index_if_exists;