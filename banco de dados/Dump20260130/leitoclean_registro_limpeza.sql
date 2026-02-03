CREATE DATABASE  IF NOT EXISTS `leitoclean` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `leitoclean`;
-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: 10.2.2.54    Database: leitoclean
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `registro_limpeza`
--

DROP TABLE IF EXISTS `registro_limpeza`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registro_limpeza` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_cartao_asg` bigint NOT NULL,
  `funcionario_asg` varchar(255) NOT NULL,
  `id_cartao_enf` bigint DEFAULT NULL,
  `funcionario_enf` varchar(255) DEFAULT NULL,
  `id_cartao_tec` bigint DEFAULT NULL,
  `funcionario_tec` varchar(255) DEFAULT NULL,
  `numero_leito` varchar(50) NOT NULL,
  `paciente` varchar(200) DEFAULT NULL,
  `setor` varchar(100) DEFAULT NULL,
  `tipo_limpeza` varchar(50) NOT NULL,
  `data_inicio` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_fim` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `vencimento` datetime DEFAULT NULL,
  `tempo_total_seconds` int DEFAULT NULL,
  `tempo_total_text` varchar(50) DEFAULT NULL,
  `ip_dispositivo` varchar(45) NOT NULL,
  `status` enum('EM_ANDAMENTO','AGUARDANDO_VALIDACAO','CONCLUIDA','PENDENTE') DEFAULT 'EM_ANDAMENTO',
  `email_enviado` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_ip_status` (`ip_dispositivo`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `registro_limpeza`
--

LOCK TABLES `registro_limpeza` WRITE;
/*!40000 ALTER TABLE `registro_limpeza` DISABLE KEYS */;
/*!40000 ALTER TABLE `registro_limpeza` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-30 20:52:52
