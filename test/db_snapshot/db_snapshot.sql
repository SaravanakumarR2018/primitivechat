-- MySQL dump 10.13  Distrib 8.0.40, for Linux (x86_64)
--
-- Host: localhost    Database: common_db
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `common_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `common_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `common_db`;

--
-- Table structure for table `customer_file_status`
--

DROP TABLE IF EXISTS `customer_file_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_file_status` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `customer_guid` varchar(255) DEFAULT NULL,
  `filename` varchar(255) DEFAULT NULL,
  `file_id` varchar(255) NOT NULL,
  `uploaded_time` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `current_activity_updated_time` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `status` enum('todo','extracted','chunked','completed','error','extract_error','chunk_error','vectorize_error','file_vectorization_failed') DEFAULT 'todo',
  `errors` text,
  `error_retry` int DEFAULT '0',
  `completed_time` timestamp(6) NULL DEFAULT NULL,
  `to_be_deleted` tinyint(1) DEFAULT '0',
  `delete_request_timestamp` timestamp(6) NULL DEFAULT NULL,
  `delete_status` enum('todo','in_progress','completed','error') DEFAULT 'todo',
  `final_delete_timestamp` timestamp(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `file_id` (`file_id`),
  KEY `idx_customer_guid` (`customer_guid`),
  KEY `idx_filename` (`filename`),
  KEY `idx_file_id` (`file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_file_status`
--

LOCK TABLES `customer_file_status` WRITE;
/*!40000 ALTER TABLE `customer_file_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `customer_file_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `org_customer_guid_mapping`
--

DROP TABLE IF EXISTS `org_customer_guid_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `org_customer_guid_mapping` (
  `org_id` varchar(255) NOT NULL,
  `customer_guid` varchar(255) NOT NULL,
  `customer_guid_org_id_map_timestamp` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `is_customer_guid_deleted` tinyint(1) DEFAULT '0',
  `delete_timestamp` timestamp(6) NULL DEFAULT NULL,
  PRIMARY KEY (`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `org_customer_guid_mapping`
--

LOCK TABLES `org_customer_guid_mapping` WRITE;
/*!40000 ALTER TABLE `org_customer_guid_mapping` DISABLE KEYS */;
INSERT INTO `org_customer_guid_mapping` VALUES ('org_2sRqEMMJlFyZSc0SfqrkHzsYsra','a0956176-c312-44b9-857a-16361f22b268','2025-04-03 09:04:17.500935',0,NULL),('org_2v9qLN6VTBGdMsq7S3yUpk7DklB','92443c3b-5cf8-47be-8228-e95568b2bcab','2025-04-03 08:38:02.372118',0,NULL);
/*!40000 ALTER TABLE `org_customer_guid_mapping` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `customer_92443c3b-5cf8-47be-8228-e95568b2bcab`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `customer_92443c3b-5cf8-47be-8228-e95568b2bcab` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `customer_92443c3b-5cf8-47be-8228-e95568b2bcab`;

--
-- Table structure for table `chat_messages`
--

DROP TABLE IF EXISTS `chat_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `chat_id` varchar(255) NOT NULL,
  `customer_guid` varchar(255) NOT NULL,
  `message` mediumtext NOT NULL,
  `sender_type` enum('customer','system') NOT NULL,
  `timestamp` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `chat_id` (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chat_messages`
--

LOCK TABLES `chat_messages` WRITE;
/*!40000 ALTER TABLE `chat_messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `chat_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `custom_field_values`
--

DROP TABLE IF EXISTS `custom_field_values`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `custom_field_values` (
  `ticket_id` bigint NOT NULL,
  PRIMARY KEY (`ticket_id`),
  CONSTRAINT `custom_field_values_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`ticket_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `custom_field_values`
--

LOCK TABLES `custom_field_values` WRITE;
/*!40000 ALTER TABLE `custom_field_values` DISABLE KEYS */;
/*!40000 ALTER TABLE `custom_field_values` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `custom_fields`
--

DROP TABLE IF EXISTS `custom_fields`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `custom_fields` (
  `field_name` varchar(255) NOT NULL,
  `field_type` varchar(255) NOT NULL,
  `required` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`field_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `custom_fields`
--

LOCK TABLES `custom_fields` WRITE;
/*!40000 ALTER TABLE `custom_fields` DISABLE KEYS */;
/*!40000 ALTER TABLE `custom_fields` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticket_comments`
--

DROP TABLE IF EXISTS `ticket_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticket_comments` (
  `comment_id` bigint NOT NULL AUTO_INCREMENT,
  `ticket_id` bigint NOT NULL,
  `posted_by` varchar(255) NOT NULL,
  `comment` text NOT NULL,
  `is_edited` tinyint(1) DEFAULT '0',
  `comment_uuid` varchar(255) DEFAULT NULL,
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`comment_id`),
  KEY `ticket_id` (`ticket_id`),
  CONSTRAINT `ticket_comments_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`ticket_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticket_comments`
--

LOCK TABLES `ticket_comments` WRITE;
/*!40000 ALTER TABLE `ticket_comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticket_comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tickets`
--

DROP TABLE IF EXISTS `tickets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tickets` (
  `ticket_id` bigint NOT NULL AUTO_INCREMENT,
  `chat_id` varchar(255) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `priority` enum('Low','Medium','High') DEFAULT 'Medium',
  `status` varchar(50) DEFAULT 'open',
  `reported_by` varchar(255) DEFAULT NULL,
  `assigned` varchar(255) DEFAULT NULL,
  `ticket_uuid` varchar(255) DEFAULT NULL,
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`ticket_id`),
  KEY `chat_id` (`chat_id`),
  CONSTRAINT `tickets_ibfk_1` FOREIGN KEY (`chat_id`) REFERENCES `chat_messages` (`chat_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tickets`
--

LOCK TABLES `tickets` WRITE;
/*!40000 ALTER TABLE `tickets` DISABLE KEYS */;
INSERT INTO `tickets` VALUES (1,NULL,'Performance issue on dashboard','API calls take longer than usual, causing delays.','Low','open','newtest102030','Unassigned','106ffa37-a164-4349-8282-149ec6fdd383','2025-04-03 09:03:13.294901','2025-04-03 09:03:13.294901'),(2,NULL,'Issue with login','The checkout button is unresponsive when clicked.','High','open','newtest102030','Unassigned','603f1618-e9c7-421b-b5e5-400317c05843','2025-04-03 09:03:13.790617','2025-04-03 09:03:13.790617'),(3,NULL,'UI issue on the homepage','Users have requested a dark mode theme for better accessibility.','Low','open','newtest102030','Unassigned','4bdb8eb5-3d32-43a0-8184-a2412ffa49ed','2025-04-03 09:03:14.524564','2025-04-03 09:03:14.524564'),(4,NULL,'User unable to access account','Data is not syncing between app and server in real-time.','Low','open','newtest102030','Unassigned','3377169d-31c0-4b95-9984-0406f2b1cf2b','2025-04-03 09:03:15.095413','2025-04-03 09:03:15.095413'),(5,NULL,'User unable to access account','The layout of the homepage is misaligned on smaller screens.','Low','open','newtest102030','Unassigned','60c53d0c-f851-40de-9f50-194d7ece0c2c','2025-04-03 09:03:15.539808','2025-04-03 09:03:15.539808'),(6,NULL,'UI issue on the homepage','User reported that their account is locked and inaccessible.','Medium','open','newtest102030','Unassigned','5fe138fd-1ab6-4bc8-bf9b-35c794b3aedd','2025-04-03 09:03:15.866673','2025-04-03 09:03:15.866673'),(7,NULL,'Performance issue on dashboard','Users have requested a dark mode theme for better accessibility.','Low','open','newtest102030','Unassigned','6a2304a9-6987-4173-94cb-ced97ba537e6','2025-04-03 09:03:16.323224','2025-04-03 09:03:16.323224'),(8,NULL,'Server downtime','Users have requested a dark mode theme for better accessibility.','Medium','open','newtest102030','Unassigned','37b47c31-8780-4409-afe7-79c5a4ff9657','2025-04-03 09:03:16.786065','2025-04-03 09:03:16.786065'),(9,NULL,'Feature request: Add dark mode','The server has been down for the past 30 minutes.','Low','open','newtest102030','Unassigned','2bd650ab-5e00-469b-83dd-f3344d05c72e','2025-04-03 09:03:17.149466','2025-04-03 09:03:17.149466'),(10,NULL,'Bug in the payment gateway','User reported that their account is locked and inaccessible.','High','open','newtest102030','Unassigned','2a65bc63-48c3-48a5-914f-d3c9826af815','2025-04-03 09:03:17.511072','2025-04-03 09:03:17.511072'),(11,NULL,'Data not syncing correctly','The server has been down for the past 30 minutes.','Medium','open','newtest102030','Unassigned','77fdd1a5-e72b-408a-9bf8-68d72c78c160','2025-04-03 09:03:18.177801','2025-04-03 09:03:18.177801'),(12,NULL,'Data not syncing correctly','Dashboard performance slows down after several filters are applied.','High','open','newtest102030','Unassigned','eb850bd3-f4f0-46c3-ba48-308ab50b47c0','2025-04-03 09:03:18.533008','2025-04-03 09:03:18.533008'),(13,NULL,'Feature request: Add dark mode','User reported that their account is locked and inaccessible.','High','open','newtest102030','Unassigned','ed0effb6-2343-4dec-9a81-276910059def','2025-04-03 09:03:18.886901','2025-04-03 09:03:18.886901'),(14,NULL,'User unable to access account','Payment processing fails intermittently for some users.','Medium','open','newtest102030','Unassigned','252459ca-962b-4c3d-8d30-284132cbfdef','2025-04-03 09:03:19.416574','2025-04-03 09:03:19.416574'),(15,NULL,'API response is slow','API calls take longer than usual, causing delays.','High','open','newtest102030','Unassigned','2db703ab-70c6-4b43-89a2-e7e8f1021ddc','2025-04-03 09:03:19.778725','2025-04-03 09:03:19.778725'),(16,NULL,'Feature request: Add dark mode','The layout of the homepage is misaligned on smaller screens.','Low','open','newtest102030','Unassigned','18e04337-2df6-4727-b2d1-5e080534fb3a','2025-04-03 09:03:20.095663','2025-04-03 09:03:20.095663'),(17,NULL,'User unable to access account','API calls take longer than usual, causing delays.','High','open','newtest102030','Unassigned','725eb6f7-2460-4998-a7ae-34cba6b8f280','2025-04-03 09:03:20.387936','2025-04-03 09:03:20.387936'),(18,NULL,'API response is slow','The server has been down for the past 30 minutes.','Low','open','newtest102030','Unassigned','cd39c57c-0b7d-444d-acc7-fda37c1ede13','2025-04-03 09:03:20.698444','2025-04-03 09:03:20.698444'),(19,NULL,'Server downtime','Payment processing fails intermittently for some users.','Medium','open','newtest102030','Unassigned','62318da4-fc2a-430d-9447-894e865a36ab','2025-04-03 09:03:21.149154','2025-04-03 09:03:21.149154'),(20,NULL,'Data not syncing correctly','Dashboard performance slows down after several filters are applied.','Medium','open','newtest102030','Unassigned','d2ebe3ac-b28c-4fa7-8ea7-8a35fe52ecf6','2025-04-03 09:03:21.534463','2025-04-03 09:03:21.534463'),(21,NULL,'User unable to access account','The layout of the homepage is misaligned on smaller screens.','Medium','open','newtest102030','Unassigned','74f5d137-bdf3-428f-bf67-923444c9596c','2025-04-03 09:03:21.973101','2025-04-03 09:03:21.973101'),(22,NULL,'Performance issue on dashboard','Users have requested a dark mode theme for better accessibility.','Low','open','newtest102030','Unassigned','82d7792d-021e-4060-a614-54bea6e630af','2025-04-03 09:03:22.379330','2025-04-03 09:03:22.379330'),(23,NULL,'Bug in the payment gateway','The checkout button is unresponsive when clicked.','Low','open','newtest102030','Unassigned','3d24fbd3-bb07-4c38-a587-dd11f8c14e4c','2025-04-03 09:03:22.736080','2025-04-03 09:03:22.736080'),(24,NULL,'Data not syncing correctly','The layout of the homepage is misaligned on smaller screens.','Medium','open','newtest102030','Unassigned','b40c7b0f-fb38-4815-a490-dc1ab89a0e73','2025-04-03 09:03:23.108243','2025-04-03 09:03:23.108243'),(25,NULL,'Server downtime','API calls take longer than usual, causing delays.','High','open','newtest102030','Unassigned','25a26525-da15-43f3-802c-fb596deac44c','2025-04-03 09:03:23.372119','2025-04-03 09:03:23.372119'),(26,NULL,'Server downtime','API calls take longer than usual, causing delays.','Medium','open','newtest102030','Unassigned','041eb103-7be0-4a72-87ef-baa8ad0aa26b','2025-04-03 09:03:23.747190','2025-04-03 09:03:23.747190'),(27,NULL,'Error in checkout process','The server has been down for the past 30 minutes.','High','open','newtest102030','Unassigned','5036f25e-594b-446c-ac23-73347e2a612a','2025-04-03 09:03:24.063073','2025-04-03 09:03:24.063073'),(28,NULL,'API response is slow','Dashboard performance slows down after several filters are applied.','High','open','newtest102030','Unassigned','fb3fd04f-b575-49ed-8698-b574f198b25f','2025-04-03 09:03:24.426371','2025-04-03 09:03:24.426371'),(29,NULL,'Error in checkout process','User reported that their account is locked and inaccessible.','Low','open','newtest102030','Unassigned','0afd4a4e-b405-438e-a280-c691b5501050','2025-04-03 09:03:24.737996','2025-04-03 09:03:24.737996'),(30,NULL,'Data not syncing correctly','User is unable to log into their account after multiple attempts.','High','open','newtest102030','Unassigned','e4168cf7-6617-4baa-8f74-95a1d7b55bc6','2025-04-03 09:03:25.136047','2025-04-03 09:03:25.136047'),(31,NULL,'UI issue on the homepage','Dashboard performance slows down after several filters are applied.','Medium','open','newtest102030','Unassigned','de7e661f-e3b3-4b02-ba7b-30e2f0819a27','2025-04-03 09:03:25.505891','2025-04-03 09:03:25.505891'),(32,NULL,'Data not syncing correctly','The layout of the homepage is misaligned on smaller screens.','High','open','newtest102030','Unassigned','81d3d6b0-7113-4a8d-a0d6-85547dbf9ffa','2025-04-03 09:03:25.933516','2025-04-03 09:03:25.933516'),(33,NULL,'Performance issue on dashboard','Dashboard performance slows down after several filters are applied.','Low','open','newtest102030','Unassigned','bd95a815-08a6-4f22-87db-7a5cd92963fc','2025-04-03 09:03:26.483460','2025-04-03 09:03:26.483460'),(34,NULL,'API response is slow','Users have requested a dark mode theme for better accessibility.','Medium','open','newtest102030','Unassigned','beb326c9-d133-413d-8a51-decbb2d0f0a2','2025-04-03 09:03:30.989772','2025-04-03 09:03:30.989772'),(35,NULL,'Server downtime','Payment processing fails intermittently for some users.','Low','open','newtest102030','Unassigned','1af8896e-3626-42ce-bfbe-07b73c2e9cb3','2025-04-03 09:03:31.406518','2025-04-03 09:03:31.406518'),(36,NULL,'Feature request: Add dark mode','User is unable to log into their account after multiple attempts.','Low','open','newtest102030','Unassigned','3918eee4-28bb-47b3-9286-0a1dceece4a7','2025-04-03 09:03:31.702584','2025-04-03 09:03:31.702584'),(37,NULL,'Error in checkout process','The layout of the homepage is misaligned on smaller screens.','Low','open','newtest102030','Unassigned','e169e284-a98a-4547-9d3b-fbfc0df174c4','2025-04-03 09:03:32.064967','2025-04-03 09:03:32.064967'),(38,NULL,'Bug in the payment gateway','Data is not syncing between app and server in real-time.','High','open','newtest102030','Unassigned','b32e7443-a008-440d-bfe2-f106b5ba67b4','2025-04-03 09:03:32.475108','2025-04-03 09:03:32.475108'),(39,NULL,'User unable to access account','User is unable to log into their account after multiple attempts.','Medium','open','newtest102030','Unassigned','dc6dc02a-bd35-45ae-9b1e-35756d151a4a','2025-04-03 09:03:32.835352','2025-04-03 09:03:32.835352'),(40,NULL,'Issue with login','Data is not syncing between app and server in real-time.','Low','open','newtest102030','Unassigned','287e167f-5fec-467c-864c-8b4fd548593c','2025-04-03 09:03:33.421575','2025-04-03 09:03:33.421575'),(41,NULL,'Server downtime','User reported that their account is locked and inaccessible.','Low','open','newtest102030','Unassigned','ca2158da-fe6d-4221-baf3-f8f3d4eda94f','2025-04-03 09:03:37.925299','2025-04-03 09:03:37.925299'),(42,NULL,'Bug in the payment gateway','The server has been down for the past 30 minutes.','High','open','newtest102030','Unassigned','9512ea21-4568-4817-a622-9633084b43d2','2025-04-03 09:03:38.335213','2025-04-03 09:03:38.335213'),(43,NULL,'Error in checkout process','User reported that their account is locked and inaccessible.','Medium','open','newtest102030','Unassigned','e16a9f57-3027-49e8-9663-0bd1ec180267','2025-04-03 09:03:38.637827','2025-04-03 09:03:38.637827'),(44,NULL,'UI issue on the homepage','The layout of the homepage is misaligned on smaller screens.','High','open','newtest102030','Unassigned','87f35a6e-9490-40f9-b1b0-d1aa87337f72','2025-04-03 09:03:39.404666','2025-04-03 09:03:39.404666'),(45,NULL,'Bug in the payment gateway','Dashboard performance slows down after several filters are applied.','High','open','newtest102030','Unassigned','4bfcbb83-c526-427c-bed5-b3ec336e3775','2025-04-03 09:03:39.867480','2025-04-03 09:03:39.867480'),(46,NULL,'UI issue on the homepage','The checkout button is unresponsive when clicked.','High','open','newtest102030','Unassigned','4afd0fc3-9d63-4c20-83ed-88cd555bd2c1','2025-04-03 09:03:40.157251','2025-04-03 09:03:40.157251'),(47,NULL,'Issue with login','Users have requested a dark mode theme for better accessibility.','Low','open','newtest102030','Unassigned','5001c57c-af99-4d0c-ab2e-0c46906802b0','2025-04-03 09:03:40.547205','2025-04-03 09:03:40.547205'),(48,NULL,'Performance issue on dashboard','The checkout button is unresponsive when clicked.','High','open','newtest102030','Unassigned','1111fe06-997b-4567-a4f1-c61c6bb87863','2025-04-03 09:03:41.070286','2025-04-03 09:03:41.070286'),(49,NULL,'Error in checkout process','User is unable to log into their account after multiple attempts.','Medium','open','newtest102030','Unassigned','8226d5e6-b171-4e87-9cfa-cb572f2cf65e','2025-04-03 09:03:41.484561','2025-04-03 09:03:41.484561'),(50,NULL,'Feature request: Add dark mode','The checkout button is unresponsive when clicked.','Low','open','newtest102030','Unassigned','d2918e4a-1ea9-432c-8510-dbe983109f25','2025-04-03 09:03:41.850806','2025-04-03 09:03:41.850806'),(51,NULL,'Bug in the payment gateway','Payment processing fails intermittently for some users.','Low','open','newtest102030','Unassigned','4d02a7bb-5371-4f11-b598-81833a6437b2','2025-04-03 09:03:42.205085','2025-04-03 09:03:42.205085'),(52,NULL,'Error in checkout process','The server has been down for the past 30 minutes.','Low','open','newtest102030','Unassigned','de57b8ba-d159-4ea4-8d7e-caf1e80a941f','2025-04-03 09:03:42.501518','2025-04-03 09:03:42.501518'),(53,NULL,'Issue with login','Payment processing fails intermittently for some users.','Low','open','newtest102030','Unassigned','67488052-765c-4ca6-943b-398ce29a0e48','2025-04-03 09:03:42.887414','2025-04-03 09:03:42.887414'),(54,NULL,'Issue with login','Payment processing fails intermittently for some users.','High','open','newtest102030','Unassigned','c34b109e-4732-4d48-ba8c-93ea3684c4cd','2025-04-03 09:03:43.249212','2025-04-03 09:03:43.249212'),(55,NULL,'Performance issue on dashboard','The checkout button is unresponsive when clicked.','Low','open','newtest102030','Unassigned','5b74966b-93ba-4d8c-aa81-f0f215530a33','2025-04-03 09:03:43.563598','2025-04-03 09:03:43.563598'),(56,NULL,'Issue with login','Payment processing fails intermittently for some users.','Low','open','newtest102030','Unassigned','c4e34152-50bf-4878-b46c-04750a792254','2025-04-03 09:03:43.877106','2025-04-03 09:03:43.877106'),(57,NULL,'Error in checkout process','API calls take longer than usual, causing delays.','High','open','newtest102030','Unassigned','87c7be15-105a-4a84-911b-4188b8b8838c','2025-04-03 09:03:44.293527','2025-04-03 09:03:44.293527'),(58,NULL,'API response is slow','User is unable to log into their account after multiple attempts.','High','open','newtest102030','Unassigned','412b4425-3341-435e-b300-4b0390a30258','2025-04-03 09:03:44.575678','2025-04-03 09:03:44.575678'),(59,NULL,'Data not syncing correctly','Dashboard performance slows down after several filters are applied.','Low','open','newtest102030','Unassigned','dcfe3cdb-1024-4683-b8b7-588b66b6c828','2025-04-03 09:03:44.953492','2025-04-03 09:03:44.953492'),(60,NULL,'Error in checkout process','The layout of the homepage is misaligned on smaller screens.','Low','open','newtest102030','Unassigned','a503a2b0-4e1c-43a9-802e-4b31d35aa2f0','2025-04-03 09:03:45.282832','2025-04-03 09:03:45.282832'),(61,NULL,'API response is slow','User reported that their account is locked and inaccessible.','Medium','open','newtest102030','Unassigned','6236c81a-d83a-4539-8135-263276ebba71','2025-04-03 09:03:45.908086','2025-04-03 09:03:45.908086'),(62,NULL,'Issue with login','The checkout button is unresponsive when clicked.','High','open','newtest102030','Unassigned','ec12d638-fdc9-4723-b2e5-42d1dd5ff248','2025-04-03 09:03:46.224241','2025-04-03 09:03:46.224241'),(63,NULL,'Bug in the payment gateway','Payment processing fails intermittently for some users.','High','open','newtest102030','Unassigned','9c1a5520-92e9-4759-ba2f-210206408a92','2025-04-03 09:03:46.471638','2025-04-03 09:03:46.471638'),(64,NULL,'Bug in the payment gateway','API calls take longer than usual, causing delays.','High','open','newtest102030','Unassigned','97611e7e-79f0-4993-b3b5-7c171b793274','2025-04-03 09:03:46.887314','2025-04-03 09:03:46.887314'),(65,NULL,'Feature request: Add dark mode','Users have requested a dark mode theme for better accessibility.','High','open','newtest102030','Unassigned','d9b7d30f-6686-4ac2-817d-8a8efcb6cf38','2025-04-03 09:03:47.296393','2025-04-03 09:03:47.296393'),(66,NULL,'UI issue on the homepage','The layout of the homepage is misaligned on smaller screens.','Medium','open','newtest102030','Unassigned','5acdfde4-4053-4209-a9fe-09a5ce259b4a','2025-04-03 09:03:47.609834','2025-04-03 09:03:47.609834'),(67,NULL,'Server downtime','User is unable to log into their account after multiple attempts.','Low','open','newtest102030','Unassigned','a4a6ca17-2dbc-406a-b25a-95cb2094070a','2025-04-03 09:03:48.000755','2025-04-03 09:03:48.000755'),(68,NULL,'Error in checkout process','Dashboard performance slows down after several filters are applied.','High','open','newtest102030','Unassigned','f27933c7-27c9-41f2-9c1c-63c2bfff0365','2025-04-03 09:03:48.848309','2025-04-03 09:03:48.848309'),(69,NULL,'Data not syncing correctly','User reported that their account is locked and inaccessible.','Medium','open','newtest102030','Unassigned','a7a1a0f5-66d2-40aa-96d1-66c2e501952a','2025-04-03 09:03:49.431035','2025-04-03 09:03:49.431035'),(70,NULL,'Data not syncing correctly','The layout of the homepage is misaligned on smaller screens.','Medium','open','newtest102030','Unassigned','7d53f138-8081-49e7-b398-4810359e0785','2025-04-03 09:03:49.764560','2025-04-03 09:03:49.764560'),(71,NULL,'Performance issue on dashboard','User reported that their account is locked and inaccessible.','Low','open','newtest102030','Unassigned','200f2e14-61e0-4432-a1a9-362ff2cc881a','2025-04-03 09:03:50.081729','2025-04-03 09:03:50.081729'),(72,NULL,'User unable to access account','The checkout button is unresponsive when clicked.','Medium','open','newtest102030','Unassigned','98119f7b-7a2d-4616-9152-acdac937f608','2025-04-03 09:03:50.460834','2025-04-03 09:03:50.460834'),(73,NULL,'Data not syncing correctly','The server has been down for the past 30 minutes.','High','open','newtest102030','Unassigned','b69979cc-acc6-4661-9399-e9063b23eb6d','2025-04-03 09:03:50.792074','2025-04-03 09:03:50.792074'),(74,NULL,'Data not syncing correctly','The checkout button is unresponsive when clicked.','Low','open','newtest102030','Unassigned','dc1e9509-6583-464e-bc1d-fe215660cd10','2025-04-03 09:03:51.124795','2025-04-03 09:03:51.124795'),(75,NULL,'Issue with login','User is unable to log into their account after multiple attempts.','High','open','newtest102030','Unassigned','ce886f16-96a8-4acc-ae92-d1b8caf70b82','2025-04-03 09:03:51.505458','2025-04-03 09:03:51.505458'),(76,NULL,'API response is slow','The checkout button is unresponsive when clicked.','Low','open','newtest102030','Unassigned','b3dc1270-dc8d-499f-97af-96c1d44b1145','2025-04-03 09:03:51.816870','2025-04-03 09:03:51.816870'),(77,NULL,'UI issue on the homepage','The checkout button is unresponsive when clicked.','Medium','open','newtest102030','Unassigned','71d8bfe1-9990-4545-9e4f-2ac23a798e05','2025-04-03 09:03:52.246643','2025-04-03 09:03:52.246643'),(78,NULL,'Bug in the payment gateway','Dashboard performance slows down after several filters are applied.','High','open','newtest102030','Unassigned','a1e14969-dcda-407f-ab82-6f335d9d8bd4','2025-04-03 09:03:52.644159','2025-04-03 09:03:52.644159'),(79,NULL,'Performance issue on dashboard','Payment processing fails intermittently for some users.','High','open','newtest102030','Unassigned','11c98e54-e925-4b07-b18a-937306fb0db9','2025-04-03 09:03:53.114381','2025-04-03 09:03:53.114381'),(80,NULL,'UI issue on the homepage','The server has been down for the past 30 minutes.','Low','open','newtest102030','Unassigned','d65be33b-1c87-4b0e-aeae-8f89dcbc1a56','2025-04-03 09:03:53.432516','2025-04-03 09:03:53.432516'),(81,NULL,'Server downtime','Payment processing fails intermittently for some users.','Medium','open','newtest102030','Unassigned','39d2fad4-b016-4bea-9df3-c00a7cd0538d','2025-04-03 09:03:53.743050','2025-04-03 09:03:53.743050'),(82,NULL,'API response is slow','Dashboard performance slows down after several filters are applied.','Low','open','newtest102030','Unassigned','8a3a9d78-4bb4-4db7-a69c-bb296631a2d6','2025-04-03 09:03:54.056402','2025-04-03 09:03:54.056402'),(83,NULL,'Feature request: Add dark mode','Payment processing fails intermittently for some users.','High','open','newtest102030','Unassigned','ce5651a4-6c6b-45b7-9bd7-b1d0abcab456','2025-04-03 09:03:54.577715','2025-04-03 09:03:54.577715'),(84,NULL,'Feature request: Add dark mode','The server has been down for the past 30 minutes.','Low','open','newtest102030','Unassigned','8347b862-a635-4a52-b15e-955ab2ea578f','2025-04-03 09:03:54.895300','2025-04-03 09:03:54.895300'),(85,NULL,'Feature request: Add dark mode','API calls take longer than usual, causing delays.','High','open','newtest102030','Unassigned','801f8c41-9600-45a8-b4f8-ab7003f4d235','2025-04-03 09:03:55.351996','2025-04-03 09:03:55.351996'),(86,NULL,'API response is slow','Dashboard performance slows down after several filters are applied.','Low','open','newtest102030','Unassigned','f413c9c5-e42c-40af-a393-419db72f71c6','2025-04-03 09:03:55.683175','2025-04-03 09:03:55.683175'),(87,NULL,'Feature request: Add dark mode','Payment processing fails intermittently for some users.','High','open','newtest102030','Unassigned','9649590b-8e70-4f61-930a-29b91df3ef4d','2025-04-03 09:03:56.117695','2025-04-03 09:03:56.117695'),(88,NULL,'Bug in the payment gateway','Users have requested a dark mode theme for better accessibility.','Low','open','newtest102030','Unassigned','f20e997d-ac14-4de5-82b3-de3d36291f19','2025-04-03 09:03:56.438282','2025-04-03 09:03:56.438282'),(89,NULL,'User unable to access account','The server has been down for the past 30 minutes.','Medium','open','newtest102030','Unassigned','8c4e5f1d-d66f-4596-b4ee-a50ea16582c4','2025-04-03 09:03:56.805847','2025-04-03 09:03:56.805847'),(90,NULL,'User unable to access account','Data is not syncing between app and server in real-time.','Medium','open','newtest102030','Unassigned','afcc112e-6009-4ab7-b30d-c7ab07004497','2025-04-03 09:03:57.235504','2025-04-03 09:03:57.235504'),(91,NULL,'API response is slow','Users have requested a dark mode theme for better accessibility.','Medium','open','newtest102030','Unassigned','cab86993-a67e-43f1-a28e-24da2bbac162','2025-04-03 09:03:57.583142','2025-04-03 09:03:57.583142'),(92,NULL,'Server downtime','Dashboard performance slows down after several filters are applied.','Low','open','newtest102030','Unassigned','4e0fc407-4fa2-49c9-a1e1-9226a5c75229','2025-04-03 09:03:57.917691','2025-04-03 09:03:57.917691'),(93,NULL,'Issue with login','User reported that their account is locked and inaccessible.','High','open','newtest102030','Unassigned','addf6442-e911-45aa-8958-f142af3fee71','2025-04-03 09:03:58.500459','2025-04-03 09:03:58.500459'),(94,NULL,'Performance issue on dashboard','The server has been down for the past 30 minutes.','High','open','newtest102030','Unassigned','65c69340-041c-4f19-8a36-eb523f31117f','2025-04-03 09:03:59.059086','2025-04-03 09:03:59.059086'),(95,NULL,'Feature request: Add dark mode','User reported that their account is locked and inaccessible.','High','open','newtest102030','Unassigned','361e1c02-56f0-4d64-a37f-73a9cdc47804','2025-04-03 09:03:59.403867','2025-04-03 09:03:59.403867'),(96,NULL,'API response is slow','The checkout button is unresponsive when clicked.','High','open','newtest102030','Unassigned','b278e680-e20e-436a-9dc5-e0c68d12709c','2025-04-03 09:03:59.736486','2025-04-03 09:03:59.736486'),(97,NULL,'Performance issue on dashboard','The checkout button is unresponsive when clicked.','High','open','newtest102030','Unassigned','7b4cfc0f-5099-423f-8592-e170685480c3','2025-04-03 09:04:00.104819','2025-04-03 09:04:00.104819'),(98,NULL,'API response is slow','The checkout button is unresponsive when clicked.','High','open','newtest102030','Unassigned','09d4a225-3678-4ca8-95a5-28d8262cec03','2025-04-03 09:04:00.413782','2025-04-03 09:04:00.413782'),(99,NULL,'Server downtime','The checkout button is unresponsive when clicked.','Medium','open','newtest102030','Unassigned','4d6e26f3-8c8e-487e-ade5-83fb6153bf56','2025-04-03 09:04:00.775355','2025-04-03 09:04:00.775355'),(100,NULL,'Bug in the payment gateway','User is unable to log into their account after multiple attempts.','Medium','open','newtest102030','Unassigned','55e935da-03b0-4d84-a9d9-2ce973989fe4','2025-04-03 09:04:01.098323','2025-04-03 09:04:01.098323');
/*!40000 ALTER TABLE `tickets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `uploadedfile_status`
--

DROP TABLE IF EXISTS `uploadedfile_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `uploadedfile_status` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `customer_guid` varchar(255) DEFAULT NULL,
  `filename` varchar(255) DEFAULT NULL,
  `file_id` varchar(255) NOT NULL,
  `uploaded_time` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `current_activity_updated_time` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `status` enum('todo','extracted','chunked','completed','error','extract_error','chunk_error','vectorize_error','file_vectorization_failed') DEFAULT 'todo',
  `errors` text,
  `error_retry` int DEFAULT '0',
  `completed_time` timestamp(6) NULL DEFAULT NULL,
  `to_be_deleted` tinyint(1) DEFAULT '0',
  `delete_request_timestamp` timestamp(6) NULL DEFAULT NULL,
  `delete_status` enum('todo','in_progress','completed','error') DEFAULT 'todo',
  `final_delete_timestamp` timestamp(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `file_id` (`file_id`),
  KEY `idx_customer_guid` (`customer_guid`),
  KEY `idx_filename` (`filename`),
  KEY `idx_file_id` (`file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `uploadedfile_status`
--

LOCK TABLES `uploadedfile_status` WRITE;
/*!40000 ALTER TABLE `uploadedfile_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `uploadedfile_status` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-03  9:16:00
