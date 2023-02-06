create table generi(
	id int not null primary key,
	nome varchar(255) 
);

create table autori(
	id int not null primary key,
	nome varchar(255) 
);

create table totems(
	id int not null primary key,
	qr_code_link varchar(255),
	maps_link varchar(500),
		 varchar (300)
);

create table scompartimenti(
	id int not null primary key,	
	totem_id int references totems(id),
	stato varchar(20) check (stato in ('libero', 'occupato', 'prenotato'))
);

create table libri(
	id int not null primary key,
	nome varchar(255),
	genere_id int references generi(id),
	autore_id int references autori(id),
	scompartimento_id int   references scompartimenti(id)
);

create table utenti(
	id int not null primary key,
	username varchar(255),
	pwd varchar(255)	
);

create table prestiti(
	id int not null primary key,
	utente_id int not null references utenti(id),
	libro_id int not null references libri(id),
	data_inizio_prestito date not null,
	data_fine_prestito date null,
	stato varchar CONSTRAINT stato_values check (stato in ('prenotato', 'prelevato', 'consegnato'))
);

CREATE SEQUENCE serialPrestiti START 4;

ALTER TABLE public.libri ADD img bytea NULL;
ALTER TABLE public.libri ADD "nfc-id" varchar NULL;