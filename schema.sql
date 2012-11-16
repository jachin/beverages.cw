drop table if exists beverage_transaction ;
create table beverage_transaction (
	  beverage_transaction_id int primary key auto_increment,
	  barcode text not null,
	  transaction_date datetime not null
);
