insert into generi values 
	(1,'Romantico'),
	(2,'Horror'),
	(3,'Thriller'),
	(4,'Narrativa');

insert into autori values(1, 'Emily Bronte'), (2, 'Harper Lee'), (3, 'Niccolò Ammaniti'), (4, 'Tiziano Sclavi');
	
insert into totems values  (1, 'qr-1', 'https://goo.gl/maps/ismPzxi1eAWPbTan7','Biblioteca Panizzi, Via Luigi Carlo Farini, Reggio Emilia, RE'), 
(2, 'qr-2','https://goo.gl/maps/P66FdLfTZEAy2Bzr8' ,'Unimore - V.le Timavo, Viale Timavo, Reggio Emilia, RE');

insert into scompartimenti values (1, 1, 'occupato'),(2, 1, 'occupato'),(3, 1, 'occupato'),(4, 2, 'occupato'),(5, 2, 'libero'),(6, 2, 'libero');

insert into utenti values (1, 'michaelbianco', 'iotLibrary'), (2, 'marc0todar0', 'iotLibrary'), (3, 'matteberto99', 'iotLibrary');

insert into libri values 
	(1,'Dylan Dog - I Nuovi Barbari', 2, 4, 1),
	(2,'Cime Tempestose', 1, 1, 2),
	(3,'Il Buio oltre la siepe', 3, 2, 3),
	(4,'Io non ho paura', 4, 3, 4);
	
delete from prestiti;
/*insert into prestiti values
	(1, 1, 1, now() ,NULL),
	(2, 1, 2, now() ,now()),
	(3, 2, 2, now() ,NULL);*/