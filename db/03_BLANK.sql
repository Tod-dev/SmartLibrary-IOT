delete from prestiti;
update libri set scompartimento_id = id;
update scompartimenti set stato='occupato' where id in (1,2,3,4);
update scompartimenti set stato='libero' where id in (5,6);