insert into genere values 
	(1,'Romantico'),
	(2,'Horror'),
	(3,'Thriller'),
	(4,'Narrativa');

insert into autore values(1, 'Emily Bronte'), (2, 'Harper Lee'), (3, 'Niccolò Ammaniti'), (4, 'Tiziano Sclavi');
	
insert into totem values  (1, 'qr-1', 0,0), (2, 'qr-2', 0,0);

insert into scompartimento values (1, 1),(2, 1),(3, 2),(4, 2);

insert into utente values (1, 'Michael', 'iotLibrary'), (2, 'Marco', 'iotLibrary'), (3, 'Matteo', 'iotLibrary');

insert into libro values 
	(1,'Dylan Dog - I Nuovi Barbari', 2, 4, 1),
	(2,'Cime Tempestose', 1, 1, 2),
	(3,'Il Buio oltre la siepe', 3, 2, 3),
	(4,'Io non ho paura', 4, 3, 4);
	
delete from prestito
insert into prestito values
	(1, 1, 1, now() ,NULL),
	(2, 1, 2, now() ,now()),
	(3, 2, 2, now() ,NULL);