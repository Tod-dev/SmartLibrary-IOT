create table genere(
	id int not null primary key,
	nome varchar(255) 
)

create table autore(
	id int not null primary key,
	nome varchar(255) 
)

create table totem(
	id int not null primary key,
	qr_code_link varchar(255),
	latitude decimal(15,10),
	longitude decimal(15,10)
)

create table scompartimento(
	id int not null primary key,	
	totem_id int references totem(id)
)

create table libro(
	id int not null primary key,
	nome varchar(255),
	genere_id int references genere(id),
	autore_id int references autore(id),
	scompartimento_id int   references scompartimento(id)
)

create table utente(
	id int not null primary key,
	username varchar(255),
	pwd varchar(255)	
)

create table prestito(
	id int not null primary key,
	utente_id int not null references utente(id),
	libro_id int not null references libro(id),
	data_inizio_prestito date not null,
	data_fine_prestito date null
)


ALTER TABLE prestito ADD COLUMN stato varchar CONSTRAINT stato_values check (stato in ('prenotato', 'prelevato', 'consegnato'));