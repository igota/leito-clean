


CREATE TABLE funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
	id_cartao CHAR(10) NOT NULL UNIQUE,
    tipo ENUM('asg', 'enfermagem') NOT NULL,
    situacao BOOLEAN DEFAULT TRUE
);

drop table funcionarios;


CREATE TABLE registro_limpeza (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_cartao_asg BIGINT NOT NULL,          -- id do asg que iniciou
    funcionario_asg VARCHAR(255) NOT NULL,
    id_cartao_enf BIGINT DEFAULT NULL,      -- id do enf que confirmou
    funcionario_enf VARCHAR(255) DEFAULT NULL,
    id_cartao_tec BIGINT DEFAULT NULL,      -- id do enf que confirmou
    funcionario_tec VARCHAR(255) DEFAULT NULL,
    numero_leito VARCHAR(50) NOT NULL,
    paciente VARCHAR(200) DEFAULT NULL,
    setor VARCHAR(100) DEFAULT NULL,
    tipo_limpeza VARCHAR(50) NOT NULL,
	data_inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	data_fim DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vencimento DATETIME DEFAULT NULL,
    tempo_total_seconds INT DEFAULT NULL,  -- tempo total em segundos (útil para cálculos)
    tempo_total_text VARCHAR(50) DEFAULT NULL, -- "00:12:34" ou "12m 34s"
    ip_dispositivo VARCHAR(45) NOT NULL,
    status ENUM('EM_ANDAMENTO', 'AGUARDANDO_VALIDACAO','CONCLUIDA','PENDENTE') DEFAULT 'EM_ANDAMENTO',
    email_enviado BOOLEAN DEFAULT 0
);

CREATE INDEX idx_ip_status ON registro_limpeza (ip_dispositivo, status);
drop table registro_limpeza;


CREATE TABLE cronograma (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prontuario VARCHAR(255),
    paciente VARCHAR(255),
    setor VARCHAR(255),
    dias_no_leito INT,
    dias_no_hospital INT,
    numero_leito VARCHAR(255),
    inicio_no_leito DATE,
    prazo_maximo_limpeza DATE,
    historico_id INT,
    diagnostico VARCHAR(255),
    FOREIGN KEY (historico_id) REFERENCES historico_cronogramas(id) on delete cascade
   
);

CREATE TABLE dispositivos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(45) NOT NULL,
    setor VARCHAR(100) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);


CREATE TABLE historico_cronogramas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

drop table cronograma;
drop table historico_cronogramas;
drop table funcionarios;
drop table registro_limpeza;
drop table dispositivos;
select * from cronograma;
select * from historico_cronogramas;
select * from funcionarios;
select * from registro_limpeza;
select * from dispositivos;
create database leitoclean;
use cronograma_limpeza;

DELETE FROM historico_cronogramas WHERE ID = 4;
ALTER TABLE cronograma
ADD COLUMN diagnostico varchar(255);


CREATE USER 'leitoclean'@'%' IDENTIFIED BY '@isghnti';
GRANT ALL PRIVILEGES ON *.* TO 'leitoclean'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

ALTER TABLE registro_limpeza
ADD UNIQUE INDEX idx_leito_em_andamento (numero_leito, status);

SHOW CREATE TABLE registro_limpeza;

-- Crie um índice composto para melhor performance
CREATE INDEX idx_leito_setor_status ON registro_limpeza (numero_leito, setor, status);


UPDATE registro_limpeza set status = "CONCLUIDA";

SELECT @@global.time_zone, @@session.time_zone;
SELECT NOW(), UTC_TIMESTAMP();


SELECT @@session.time_zone, @@global.time_zone;
SELECT NOW(), UTC_TIMESTAMP(), CONVERT_TZ(NOW(), @@session.time_zone, 'UTC');

ALTER TABLE registro_limpeza
MODIFY data_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY data_fim    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;





