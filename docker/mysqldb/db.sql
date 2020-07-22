-- MySQL dump 10.13  Distrib 5.7.29, for Linux (x86_64)
--
-- Host: localhost    Database: earkdb
-- ------------------------------------------------------
-- Server version	5.7.29-0ubuntu0.18.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_group_id_b120cbf9` (`group_id`),
  KEY `auth_group_permissions_permission_id_84c5c92e` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id_2f476e4b` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=57 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add information package',7,'add_informationpackage'),(26,'Can change information package',7,'change_informationpackage'),(27,'Can delete information package',7,'delete_informationpackage'),(28,'Can view information package',7,'view_informationpackage'),(29,'Can add test model',8,'add_testmodel'),(30,'Can change test model',8,'change_testmodel'),(31,'Can delete test model',8,'delete_testmodel'),(32,'Can view test model',8,'view_testmodel'),(33,'Can add uploaded file',9,'add_uploadedfile'),(34,'Can change uploaded file',9,'change_uploadedfile'),(35,'Can delete uploaded file',9,'delete_uploadedfile'),(36,'Can view uploaded file',9,'view_uploadedfile'),(37,'Can add representation',10,'add_representation'),(38,'Can change representation',10,'change_representation'),(39,'Can delete representation',10,'delete_representation'),(40,'Can view representation',10,'view_representation'),(41,'Can add internal identifier',11,'add_internalidentifier'),(42,'Can change internal identifier',11,'change_internalidentifier'),(43,'Can delete internal identifier',11,'delete_internalidentifier'),(44,'Can view internal identifier',11,'view_internalidentifier'),(45,'Can add eark user',12,'add_earkuser'),(46,'Can change eark user',12,'change_earkuser'),(47,'Can delete eark user',12,'delete_earkuser'),(48,'Can view eark user',12,'view_earkuser'),(49,'Can add Token',13,'add_token'),(50,'Can change Token',13,'change_token'),(51,'Can delete Token',13,'delete_token'),(52,'Can view Token',13,'view_token'),(53,'Can add API key',14,'add_apikey'),(54,'Can change API key',14,'change_apikey'),(55,'Can delete API key',14,'delete_apikey'),(56,'Can view API key',14,'view_apikey');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$180000$gfyyRJOGH9ZQ$bje1jm93zmOEPhf2odD5k9GNiM/Mwf9Fs/KMZXcu8Hw=','2020-07-20 12:52:20.093630',1,'admin','','','',1,1,'2020-03-20 22:01:42.000000');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_user_id_6a12ed8b` (`user_id`),
  KEY `auth_user_groups_group_id_97559544` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_user_id_a95ead1b` (`user_id`),
  KEY `auth_user_user_permissions_permission_id_1fbb5f2c` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `authtoken_token`
--

DROP TABLE IF EXISTS `authtoken_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `authtoken_token` (
  `key` varchar(40) NOT NULL,
  `created` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`key`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `authtoken_token`
--

LOCK TABLES `authtoken_token` WRITE;
/*!40000 ALTER TABLE `authtoken_token` DISABLE KEYS */;
INSERT INTO `authtoken_token` VALUES ('325dfabc9839904a117d446440232abaf344f9a0','2020-02-27 14:08:04.917407',1);
/*!40000 ALTER TABLE `authtoken_token` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2020-03-06 13:51:30.732866','9DUG2D3J.pbkdf2_sha256$180000$c6N7boVvNAgF$ulzHPIX9fKEBEUnB109Q2CXUfF8XN/trUwf/BTg6ShE=','eark4you',1,'[{\"added\": {}}]',14,1),(2,'2020-03-06 13:51:51.347963','9DUG2D3J.pbkdf2_sha256$180000$c6N7boVvNAgF$ulzHPIX9fKEBEUnB109Q2CXUfF8XN/trUwf/BTg6ShE=','eark4you',3,'',14,1),(3,'2020-03-06 13:52:02.691945','sBafmMkE.pbkdf2_sha256$180000$0zwtPJVzT7en$gaBPaRyQsfsNxp6luUp4IJt35k9r7saDbbwTigTSHE0=','backend',1,'[{\"added\": {}}]',14,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(2,'auth','permission'),(3,'auth','group'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session'),(7,'earkweb','informationpackage'),(8,'earkweb','testmodel'),(9,'earkweb','uploadedfile'),(10,'earkweb','representation'),(11,'earkweb','internalidentifier'),(12,'earkweb','earkuser'),(13,'authtoken','token'),(14,'rest_framework_api_key','apikey');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=26 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2020-02-27 14:07:27.086276'),(2,'auth','0001_initial','2020-02-27 14:07:27.126809'),(3,'admin','0001_initial','2020-02-27 14:07:27.176387'),(4,'admin','0002_logentry_remove_auto_add','2020-02-27 14:07:27.194363'),(5,'admin','0003_logentry_add_action_flag_choices','2020-02-27 14:07:27.204577'),(6,'contenttypes','0002_remove_content_type_name','2020-02-27 14:07:27.223567'),(7,'auth','0002_alter_permission_name_max_length','2020-02-27 14:07:27.227686'),(8,'auth','0003_alter_user_email_max_length','2020-02-27 14:07:27.234027'),(9,'auth','0004_alter_user_username_opts','2020-02-27 14:07:27.239210'),(10,'auth','0005_alter_user_last_login_null','2020-02-27 14:07:27.246315'),(11,'auth','0006_require_contenttypes_0002','2020-02-27 14:07:27.247016'),(12,'auth','0007_alter_validators_add_error_messages','2020-02-27 14:07:27.252201'),(13,'auth','0008_alter_user_username_max_length','2020-02-27 14:07:27.258876'),(14,'auth','0009_alter_user_last_name_max_length','2020-02-27 14:07:27.266110'),(15,'auth','0010_alter_group_name_max_length','2020-02-27 14:07:27.273715'),(16,'auth','0011_update_proxy_permissions','2020-02-27 14:07:27.279040'),(17,'authtoken','0001_initial','2020-02-27 14:07:27.286687'),(18,'authtoken','0002_auto_20160226_1747','2020-02-27 14:07:27.306076'),(19,'earkweb','0001_initial','2020-02-27 14:07:27.354229'),(20,'sessions','0001_initial','2020-02-27 14:07:27.371504'),(21,'earkweb','0002_informationpackage_basic_metadata','2020-02-27 14:32:51.098884'),(22,'rest_framework_api_key','0001_initial','2020-03-06 13:42:07.474049'),(23,'rest_framework_api_key','0002_auto_20190529_2243','2020-03-06 13:42:07.489194'),(24,'rest_framework_api_key','0003_auto_20190623_1952','2020-03-06 13:42:07.491397'),(25,'rest_framework_api_key','0004_prefix_hashed_key','2020-03-06 13:42:07.547123');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('rlt0nnjjal7rbao7zf8kwisrj8ae4acc','NDE1M2RhOTJkYTk4NzFiMWU5ZDY1OTUwZGY5ZTJmMDhmMzU4OTIxNDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwiX2xhbmd1YWdlIjoiZGUiLCJzdGVwMSI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoiOEdIelp3Mlh1NlZxOXA3MHlsdzJzaUxvV1BFR3I5U2d5N3g5RGtIMndoZVBZWXMxWWluNHBoMWY2YVExcXNtSiIsInRpdGxlIjoidGVzdCB0aXRsZSIsImRlc2NyaXB0aW9uIjoiZGVzY3JpcHRpb24iLCJ0YWdzIjoiW10iLCJ1c2VyX2dlbmVyYXRlZF90YWdzIjoiW10ifSwic3RlcDIiOnsiY3NyZm1pZGRsZXdhcmV0b2tlbiI6IlFwYnhtOVE5ZFhwazN0bXlXYVdVWlg5RE9WcDRCa1dLZ1ExNzBYdmVmOElKUzJIem03TldXV3B1WWdCcEFEcWQiLCJjb250YWN0X3BvaW50IjoiVGVzdHByb3ZpZGVyIiwiY29udGFjdF9lbWFpbCI6InRlc3Rwcm92aWRlckBkYXRhbWFya2V0LmF0IiwicHVibGlzaGVyIjoiVGVzdHByb3ZpZGVyIiwicHVibGlzaGVyX2VtYWlsIjoidGVzdHByb3ZpZGVyQGRhdGFtYXJrZXQuYXQiLCJsYW5ndWFnZSI6IkVuZ2xpc2gifSwiZGlzdHJpYnV0aW9ucyI6bnVsbCwibWRfcHJvcGVydGllcyI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoiUzludVkzdE1MckpEZkNIamRtWlB5N01OdXdMbnNsWWFpQWQ0Q1I4Uk5DMjI0YjJrRGpRUnY2MkVFUlhJckVzRCIsInRpdGxlIjoidGVzdCB0aXRsZSIsImRlc2NyaXB0aW9uIjoiZGVzY3JpcHRpb24iLCJ0YWdzIjoiW10iLCJ1c2VyX2dlbmVyYXRlZF90YWdzIjoiW10iLCJjb250YWN0X3BvaW50IjoiVGVzdHByb3ZpZGVyIiwiY29udGFjdF9lbWFpbCI6InRlc3Rwcm92aWRlckBkYXRhbWFya2V0LmF0IiwicHVibGlzaGVyIjoiVGVzdHByb3ZpZGVyIiwicHVibGlzaGVyX2VtYWlsIjoidGVzdHByb3ZpZGVyQGRhdGFtYXJrZXQuYXQiLCJsYW5ndWFnZSI6IkVuZ2xpc2giLCJpZGVudGlmaWVyIjoiNTYxZjNlOGMtY2FhOC00OTc4LTg0M2QtYzNjNWVhMGZiMmRlIiwiY3VycmRhdGUiOiIyMDIwLTAyLTI3VDE2OjMyOjA4WiIsImxhc3RfY2hhbmdlIjoiMjAyMC0wMi0yN1QxNjozMjowOFoiLCJjcmVhdGVkIjoiMjAyMC0wMi0yN1QxNjozMjowOFoiLCJkamFuZ29fc2VydmljZV9ob3N0IjoiMTI3LjAuMC4xIiwiZGphbmdvX3NlcnZpY2VfcG9ydCI6ODAwMCwibGFuZGluZ19wYWdlIjoiaHR0cDovLzEyNy4wLjAuMTo4MDAwL2Vhcmt3ZWIvYWNjZXNzL2RhdGFzZXQvNTYxZjNlOGMtY2FhOC00OTc4LTg0M2QtYzNjNWVhMGZiMmRlLyIsIm5vZGVfbmFtZXNwYWNlX2lkIjoiZG1hIiwicmVwb19pZGVudGlmaWVyIjoiaW5mbzpkbWEvYWl0OnJlcG9zaXRvcnkxIiwicmVwb190aXRsZSI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2Rlc2NyaXB0aW9uIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fY2F0YWxvZ3VlX2lzc3VlZCI6IjIwMjAtMDEtMDFUMTI6MDA6MDBaIiwicmVwb19jYXRhbG9ndWVfbW9kaWZpZWQiOiIyMDIwLTAyLTAxVDEyOjAwOjAwWiIsImxhbmdfYWxwaGFfMyI6ImVuZyJ9fQ==','2020-03-12 16:56:50.824966'),('4ycch1hd99r19q6oohm6ysv5twqidns3','OGExMGI0MmI5YWU1ZmUzNmFiNDJmNWE3YzYwNDEwMzZhY2IwZWI5NDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJwcm9jZXNzX2lkIjoiY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5IiwiZGlzdHJpYnV0aW9ucyI6bnVsbCwicmVwcmVzZW50YXRpb25zIjpudWxsLCJfbGFuZ3VhZ2UiOiJlbiIsIm1kX3Byb3BlcnRpZXMiOnsiY3NyZm1pZGRsZXdhcmV0b2tlbiI6InJqcXBUUEYzbG5nU3dGVmowdjVZdVhhaWFMZ1NtemNwMUFOWjFYUVF3MDliSGpQUUo2SUtjcW0ySldFRDM2WnciLCJ0aXRsZSI6InRlc3QgdGl0bGUiLCJkZXNjcmlwdGlvbiI6InRlc3QgZGVzY3JpcHRpb24gbmVlZHMgdG8gYmUgZXh0ZW5kZWQiLCJ0YWdzIjoiW10iLCJ1c2VyX2dlbmVyYXRlZF90YWdzIjoiW10iLCJjb250YWN0X3BvaW50IjoiVGVzdHByb3ZpZGVyIiwiY29udGFjdF9lbWFpbCI6InRlc3Rwcm92aWRlckBlYXJrLXByb2plY3QuY29tIiwicHVibGlzaGVyIjoiVGVzdHByb3ZpZGVyIiwicHVibGlzaGVyX2VtYWlsIjoidGVzdHByb3ZpZGVyQGVhcmstcHJvamVjdC5jb20iLCJsYW5ndWFnZSI6IkVuZ2xpc2giLCJpZGVudGlmaWVyIjoiY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5IiwiY3VycmRhdGUiOiIyMDIwLTAyLTI4VDE2OjE0OjEyWiIsImxhc3RfY2hhbmdlIjoiMjAyMC0wMi0yOFQxNjoxNDoxMloiLCJjcmVhdGVkIjoiMjAyMC0wMi0yOFQxNjoxNDoxMloiLCJkamFuZ29fc2VydmljZV9ob3N0IjoibG9jYWxob3N0IiwiZGphbmdvX3NlcnZpY2VfcG9ydCI6ODAwMCwibGFuZGluZ19wYWdlIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2Vhcmt3ZWIvYWNjZXNzL2RhdGFzZXQvY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5LyIsInJlcHJlc2VudGF0aW9ucyI6eyJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6InBkZiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IlBERiByZXByZXNlbnRhdGlvbiIsImFjY2Vzc19yaWdodHMiOiJmcmVlIn0sIm5mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoicG5nIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiUE5HIGZpbGVzIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUifX0sIm5vZGVfbmFtZXNwYWNlX2lkIjoiZWFyayIsInJlcG9faWRlbnRpZmllciI6ImluZm86ZG1hL2FpdDpyZXBvc2l0b3J5MSIsInJlcG9fdGl0bGUiOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19kZXNjcmlwdGlvbiI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2NhdGFsb2d1ZV9pc3N1ZWQiOiIyMDIwLTAxLTAxVDEyOjAwOjAwWiIsInJlcG9fY2F0YWxvZ3VlX21vZGlmaWVkIjoiMjAyMC0wMi0wMVQxMjowMDowMFoiLCJsYW5nX2FscGhhXzMiOiJlbmcifX0=','2020-03-13 15:40:59.302865'),('n03m6fwdlgz6b11dxd8cifmm3noza2yt','OTZiNWQ5MjAzYWE5MmU3ODkzMmY0YWNiYWMzNzM3YTYwOTdlZTA3ZDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJyZXByZXNlbnRhdGlvbnMiOm51bGwsInByb2Nlc3NfaWQiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJfbGFuZ3VhZ2UiOiJkZSIsIm1kX3Byb3BlcnRpZXMiOnsiY3NyZm1pZGRsZXdhcmV0b2tlbiI6InV0TzNydmdDR3pkcHI3djJ1SlRjRjRjNDdiMFlmWXZDcDQwN3NHWGlmREdhYkpIeXpZSFFKc1ljY2N0SzI5NU0iLCJ0aXRsZSI6InRlc3QgdGl0bGUiLCJkZXNjcmlwdGlvbiI6InRlc3QgZGVzY3JpcHRpb24gbmVlZHMgdG8gYmUgZXh0ZW5kZWQiLCJ0YWdzIjoiW10iLCJ1c2VyX2dlbmVyYXRlZF90YWdzIjoiW10iLCJjb250YWN0X3BvaW50IjoiVGVzdHByb3ZpZGVyIiwiY29udGFjdF9lbWFpbCI6InRlc3Rwcm92aWRlckBlYXJrLXByb2plY3QuY29tIiwicHVibGlzaGVyIjoiVGVzdHByb3ZpZGVyIiwicHVibGlzaGVyX2VtYWlsIjoidGVzdHByb3ZpZGVyQGVhcmstcHJvamVjdC5jb20iLCJsYW5ndWFnZSI6IkVuZ2xpc2giLCJpZGVudGlmaWVyIjoiY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5IiwiY3VycmRhdGUiOiIyMDIwLTAyLTI4VDE5OjI2OjIwWiIsImxhc3RfY2hhbmdlIjoiMjAyMC0wMi0yOFQxOToyNjoyMFoiLCJjcmVhdGVkIjoiMjAyMC0wMi0yOFQxOToyNjoyMFoiLCJkamFuZ29fc2VydmljZV9ob3N0IjoibG9jYWxob3N0IiwiZGphbmdvX3NlcnZpY2VfcG9ydCI6ODAwMCwibGFuZGluZ19wYWdlIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2Vhcmt3ZWIvYWNjZXNzL2RhdGFzZXQvY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5LyIsInJlcHJlc2VudGF0aW9ucyI6eyJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6InBkZiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IlBERiByZXByZXNlbnRhdGlvbiIsImFjY2Vzc19yaWdodHMiOiJmcmVlIn0sIm5mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgudGFyIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6IiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IiIsImFjY2Vzc19yaWdodHMiOiIifSwibmZ0b2tjbXpicWZ4bHppYWd3Y3V4YmpmcGRsZmRmdmNzb2xvbmZtaCI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJwbmciLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJQTkcgZmlsZXMiLCJhY2Nlc3NfcmlnaHRzIjoiZnJlZSJ9LCJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxLnRhciI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiIiLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiIiLCJhY2Nlc3NfcmlnaHRzIjoiIn19LCJub2RlX25hbWVzcGFjZV9pZCI6ImVhcmsiLCJyZXBvX2lkZW50aWZpZXIiOiJpbmZvOmRtYS9haXQ6cmVwb3NpdG9yeTEiLCJyZXBvX3RpdGxlIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fZGVzY3JpcHRpb24iOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19jYXRhbG9ndWVfaXNzdWVkIjoiMjAyMC0wMS0wMVQxMjowMDowMFoiLCJyZXBvX2NhdGFsb2d1ZV9tb2RpZmllZCI6IjIwMjAtMDItMDFUMTI6MDA6MDBaIiwibGFuZ19hbHBoYV8zIjoiZW5nIn19','2020-03-13 21:39:27.542831'),('twmzh880kg6uyjbk4d7hwhg1x54bfjtm','Mzg0MjY0OWNhNTJlZjhlOTM3YjRjMjE3NjI2NzFhMmEwYjcwNmYxOTp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwibWRfcHJvcGVydGllcyI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoidjJWQW05dGQ3YmFMa0dNWk42MDRxSTZpdzdSTzZlc0RxRDdFbmthVEdmRHc0aVl2U2xPSXU2U3FCOGtBVHAyTiIsInRpdGxlIjoidGVzdCB0aXRsZSIsImRlc2NyaXB0aW9uIjoidGVzdCBkZXNjcmlwdGlvbiBuZWVkcyB0byBiZSBleHRlbmRlZCIsInRhZ3MiOiJbXSIsInVzZXJfZ2VuZXJhdGVkX3RhZ3MiOiJbXSIsImNvbnRhY3RfcG9pbnQiOiJUZXN0cHJvdmlkZXIiLCJjb250YWN0X2VtYWlsIjoidGVzdHByb3ZpZGVyQGVhcmstcHJvamVjdC5jb20iLCJwdWJsaXNoZXIiOiJUZXN0cHJvdmlkZXIiLCJwdWJsaXNoZXJfZW1haWwiOiJ0ZXN0cHJvdmlkZXJAZWFyay1wcm9qZWN0LmNvbSIsImxhbmd1YWdlIjoiRW5nbGlzaCIsImlkZW50aWZpZXIiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJjdXJyZGF0ZSI6IjIwMjAtMDItMjhUMjI6MTE6NDlaIiwibGFzdF9jaGFuZ2UiOiIyMDIwLTAyLTI4VDIyOjExOjQ5WiIsImNyZWF0ZWQiOiIyMDIwLTAyLTI4VDIyOjExOjQ5WiIsImRqYW5nb19zZXJ2aWNlX2hvc3QiOiJsb2NhbGhvc3QiLCJkamFuZ29fc2VydmljZV9wb3J0Ijo4MDAwLCJsYW5kaW5nX3BhZ2UiOiJodHRwOi8vbG9jYWxob3N0OjgwMDAvZWFya3dlYi9hY2Nlc3MvZGF0YXNldC9jZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkvIiwicmVwcmVzZW50YXRpb25zIjp7ImRic2huZmR2YnJ3bHFueW50Y29mcWViZWVoaWdob3JsbWtodmF5anEiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoicGRmIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiUERGIHJlcHJlc2VudGF0aW9uIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUifSwibmZ0b2tjbXpicWZ4bHppYWd3Y3V4YmpmcGRsZmRmdmNzb2xvbmZtaC50YXIiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoiIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiIiwiYWNjZXNzX3JpZ2h0cyI6IiJ9LCJuZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6InBuZyIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IlBORyBmaWxlcyIsImFjY2Vzc19yaWdodHMiOiJmcmVlIn0sImRic2huZmR2YnJ3bHFueW50Y29mcWViZWVoaWdob3JsbWtodmF5anEudGFyIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6IiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IiIsImFjY2Vzc19yaWdodHMiOiIifX0sIm5vZGVfbmFtZXNwYWNlX2lkIjoiZWFyayIsInJlcG9faWRlbnRpZmllciI6ImluZm86ZG1hL2FpdDpyZXBvc2l0b3J5MSIsInJlcG9fdGl0bGUiOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19kZXNjcmlwdGlvbiI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2NhdGFsb2d1ZV9pc3N1ZWQiOiIyMDIwLTAxLTAxVDEyOjAwOjAwWiIsInJlcG9fY2F0YWxvZ3VlX21vZGlmaWVkIjoiMjAyMC0wMi0wMVQxMjowMDowMFoiLCJsYW5nX2FscGhhXzMiOiJlbmcifSwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJyZXByZXNlbnRhdGlvbnMiOm51bGx9','2020-03-13 21:42:41.574179'),('fh27hcra9e2p34bhhlr0dpmb8vnxyjg2','ODZmYzkwYTU0NmZhNTc4MTZmMzFkMTdkYzE2NmVlY2ZhZDFjYTUxYjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwibWRfcHJvcGVydGllcyI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoiUGE2aTNSZk9XcUo1MXFZS1RYTDIzcXJyWUYwRUZOWjBraDRKTDRmR1JpV2phSzlNVHMyZ1ZGTTFtaUtPWTFnYSIsInRpdGxlIjoidGVzdCB0aXRsZSIsImRlc2NyaXB0aW9uIjoidGVzdCBkZXNjcmlwdGlvbiBuZWVkcyB0byBiZSBleHRlbmRlZCIsInRhZ3MiOiJbXSIsInVzZXJfZ2VuZXJhdGVkX3RhZ3MiOiJbXSIsImNvbnRhY3RfcG9pbnQiOiJUZXN0cHJvdmlkZXIiLCJjb250YWN0X2VtYWlsIjoidGVzdHByb3ZpZGVyQGVhcmstcHJvamVjdC5jb20iLCJwdWJsaXNoZXIiOiJUZXN0cHJvdmlkZXIiLCJwdWJsaXNoZXJfZW1haWwiOiJ0ZXN0cHJvdmlkZXJAZWFyay1wcm9qZWN0LmNvbSIsImxhbmd1YWdlIjoiRW5nbGlzaCIsImlkZW50aWZpZXIiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJjdXJyZGF0ZSI6IjIwMjAtMDItMjhUMjI6NDE6NTJaIiwibGFzdF9jaGFuZ2UiOiIyMDIwLTAyLTI4VDIyOjQxOjUyWiIsImNyZWF0ZWQiOiIyMDIwLTAyLTI4VDIyOjQxOjUyWiIsImRqYW5nb19zZXJ2aWNlX2hvc3QiOiJsb2NhbGhvc3QiLCJkamFuZ29fc2VydmljZV9wb3J0Ijo4MDAwLCJsYW5kaW5nX3BhZ2UiOiJodHRwOi8vbG9jYWxob3N0OjgwMDAvZWFya3dlYi9hY2Nlc3MvZGF0YXNldC9jZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkvIiwicmVwcmVzZW50YXRpb25zIjp7ImRic2huZmR2YnJ3bHFueW50Y29mcWViZWVoaWdob3JsbWtodmF5anEiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoicGRmIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiUERGIHJlcHJlc2VudGF0aW9uIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUifSwibmZ0b2tjbXpicWZ4bHppYWd3Y3V4YmpmcGRsZmRmdmNzb2xvbmZtaC50YXIiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoiIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiIiwiYWNjZXNzX3JpZ2h0cyI6IiJ9LCJuZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6InBuZyIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IlBORyBmaWxlcyIsImFjY2Vzc19yaWdodHMiOiJmcmVlIn0sImRic2huZmR2YnJ3bHFueW50Y29mcWViZWVoaWdob3JsbWtodmF5anEudGFyIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6IiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IiIsImFjY2Vzc19yaWdodHMiOiIifX0sIm5vZGVfbmFtZXNwYWNlX2lkIjoiZWFyayIsInJlcG9faWRlbnRpZmllciI6ImluZm86ZG1hL2FpdDpyZXBvc2l0b3J5MSIsInJlcG9fdGl0bGUiOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19kZXNjcmlwdGlvbiI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2NhdGFsb2d1ZV9pc3N1ZWQiOiIyMDIwLTAxLTAxVDEyOjAwOjAwWiIsInJlcG9fY2F0YWxvZ3VlX21vZGlmaWVkIjoiMjAyMC0wMi0wMVQxMjowMDowMFoiLCJsYW5nX2FscGhhXzMiOiJlbmcifSwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJyZXByZXNlbnRhdGlvbnMiOm51bGx9','2020-03-13 21:53:00.339502'),('pdvzp44ww801qcpus97ywfxzu3biwkvw','MDYzYjQzYmU4MDBlMjBkMWFiM2EyZWI2MTZiNGFmMGMyNzE2M2E3Zjp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJyZXByZXNlbnRhdGlvbnMiOm51bGwsInByb2Nlc3NfaWQiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJtZF9wcm9wZXJ0aWVzIjp7ImNzcmZtaWRkbGV3YXJldG9rZW4iOiI0TmZyQ29YZE1PRUZFb3ZtaVBtYmpzZXNYSEt6NlNxZXFBZVJRRml1aWtXVWJCQ1dndEpMY2tGNjdacjdVRHJvIiwidGl0bGUiOiJ0ZXN0IHRpdGxlIiwiZGVzY3JpcHRpb24iOiJ0ZXN0IGRlc2NyaXB0aW9uIG5lZWRzIHRvIGJlIGV4dGVuZGVkIiwidGFncyI6IltdIiwidXNlcl9nZW5lcmF0ZWRfdGFncyI6IltdIiwiY29udGFjdF9wb2ludCI6IlRlc3Rwcm92aWRlciIsImNvbnRhY3RfZW1haWwiOiJ0ZXN0cHJvdmlkZXJAZWFyay1wcm9qZWN0LmNvbSIsInB1Ymxpc2hlciI6IlRlc3Rwcm92aWRlciIsInB1Ymxpc2hlcl9lbWFpbCI6InRlc3Rwcm92aWRlckBlYXJrLXByb2plY3QuY29tIiwibGFuZ3VhZ2UiOiJFbmdsaXNoIiwiaWRlbnRpZmllciI6ImNkOWU2ZWU4LWRmYjMtNDhjNC04MzRjLTg1ZDFjZmI3MDdiOSIsImN1cnJkYXRlIjoiMjAyMC0wMy0wMVQyMTowMjozMVoiLCJsYXN0X2NoYW5nZSI6IjIwMjAtMDMtMDFUMjE6MDI6MzFaIiwiY3JlYXRlZCI6IjIwMjAtMDMtMDFUMjE6MDI6MzFaIiwiZGphbmdvX3NlcnZpY2VfaG9zdCI6ImxvY2FsaG9zdCIsImRqYW5nb19zZXJ2aWNlX3BvcnQiOjgwMDAsImxhbmRpbmdfcGFnZSI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC9lYXJrd2ViL2FjY2Vzcy9kYXRhc2V0L2NkOWU2ZWU4LWRmYjMtNDhjNC04MzRjLTg1ZDFjZmI3MDdiOS8iLCJyZXByZXNlbnRhdGlvbnMiOnsiZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcSI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJwZGYiLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJQREYgcmVwcmVzZW50YXRpb24iLCJhY2Nlc3NfcmlnaHRzIjoiZnJlZSJ9LCJuZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oLnRhciI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiIiLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiIiLCJhY2Nlc3NfcmlnaHRzIjoiIn0sIm5mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoicG5nIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiUE5HIGZpbGVzIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUifSwiZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcS50YXIiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoiIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiIiwiYWNjZXNzX3JpZ2h0cyI6IiJ9fSwibm9kZV9uYW1lc3BhY2VfaWQiOiJlYXJrIiwicmVwb19pZGVudGlmaWVyIjoiaW5mbzpkbWEvYWl0OnJlcG9zaXRvcnkxIiwicmVwb190aXRsZSI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2Rlc2NyaXB0aW9uIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fY2F0YWxvZ3VlX2lzc3VlZCI6IjIwMjAtMDEtMDFUMTI6MDA6MDBaIiwicmVwb19jYXRhbG9ndWVfbW9kaWZpZWQiOiIyMDIwLTAyLTAxVDEyOjAwOjAwWiIsImxhbmdfYWxwaGFfMyI6ImVuZyJ9fQ==','2020-03-15 20:04:19.767593'),('kxph9t0eq3gkurl10ejo2p75wsr28gi3','NjJmNDI1MzM3OWNkYzczNmI1OTRmYjE1Yjc1N2U1ZWUwZTE0OTM5YTp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJyZXByZXNlbnRhdGlvbnMiOm51bGwsInByb2Nlc3NfaWQiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJtZF9wcm9wZXJ0aWVzIjp7ImNzcmZtaWRkbGV3YXJldG9rZW4iOiJjMFVUNHFsZlhFWk9mYjA5WEpIT2FJSXhpRElYemdJZ2tNVktLRGxiNU9IdkpMN2l2b1VlRTFvQ2t3WGNVNTZKIiwidGl0bGUiOiJ0ZXN0IHRpdGxlIiwiZGVzY3JpcHRpb24iOiJ0ZXN0IGRlc2NyaXB0aW9uIG5lZWRzIHRvIGJlIGV4dGVuZGVkIiwidGFncyI6IltdIiwidXNlcl9nZW5lcmF0ZWRfdGFncyI6IltdIiwiY29udGFjdF9wb2ludCI6IlRlc3Rwcm92aWRlciIsImNvbnRhY3RfZW1haWwiOiJ0ZXN0cHJvdmlkZXJAZWFyay1wcm9qZWN0LmNvbSIsInB1Ymxpc2hlciI6IlRlc3Rwcm92aWRlciIsInB1Ymxpc2hlcl9lbWFpbCI6InRlc3Rwcm92aWRlckBlYXJrLXByb2plY3QuY29tIiwibGFuZ3VhZ2UiOiJFbmdsaXNoIiwiaWRlbnRpZmllciI6ImNkOWU2ZWU4LWRmYjMtNDhjNC04MzRjLTg1ZDFjZmI3MDdiOSIsImN1cnJkYXRlIjoiMjAyMC0wMy0wNFQxNTo0NjoxNVoiLCJkYXRlIjoiMDQuMDMuMjAyMCIsImxhc3RfY2hhbmdlIjoiMjAyMC0wMy0wNFQxNTo0NjoxNVoiLCJjcmVhdGVkIjoiMjAyMC0wMy0wNFQxNTo0NjoxNVoiLCJkamFuZ29fc2VydmljZV9ob3N0IjoibG9jYWxob3N0IiwiZGphbmdvX3NlcnZpY2VfcG9ydCI6ODAwMCwibGFuZGluZ19wYWdlIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2Vhcmt3ZWIvYWNjZXNzL2RhdGFzZXQvY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5LyIsInJlcHJlc2VudGF0aW9ucyI6eyJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6InBkZiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IlBERiByZXByZXNlbnRhdGlvbiIsImFjY2Vzc19yaWdodHMiOiJmcmVlIiwiZmlsZV9pdGVtcyI6WyJyZXByZXNlbnRhdGlvbnMvZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcS9kYXRhL3RpY2tldHMucGRmIiwicmVwcmVzZW50YXRpb25zL2Ric2huZmR2YnJ3bHFueW50Y29mcWViZWVoaWdob3JsbWtodmF5anEvZGF0YS9iZXN0ZWxsdW5nLXN0cmlja2phY2tlLnBkZiJdfSwibmZ0b2tjbXpicWZ4bHppYWd3Y3V4YmpmcGRsZmRmdmNzb2xvbmZtaCI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJwbmciLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJQTkcgZmlsZXMiLCJhY2Nlc3NfcmlnaHRzIjoiZnJlZSIsImZpbGVfaXRlbXMiOlsicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS90aWNrZXRzLTEucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS90aWNrZXRzLTIucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS90aWNrZXRzLTAucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS9iZXN0ZWxsdW5nLXN0cmlja2phY2tlLTEucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS9iZXN0ZWxsdW5nLXN0cmlja2phY2tlLTAucG5nIl19LCJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxX21pZy0xIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6IiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IiIsImFjY2Vzc19yaWdodHMiOiIiLCJmaWxlX2l0ZW1zIjpbXX19LCJub2RlX25hbWVzcGFjZV9pZCI6ImVhcmsiLCJyZXBvX2lkZW50aWZpZXIiOiJpbmZvOmRtYS9haXQ6cmVwb3NpdG9yeTEiLCJyZXBvX3RpdGxlIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fZGVzY3JpcHRpb24iOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19jYXRhbG9ndWVfaXNzdWVkIjoiMjAyMC0wMS0wMVQxMjowMDowMFoiLCJyZXBvX2NhdGFsb2d1ZV9tb2RpZmllZCI6IjIwMjAtMDItMDFUMTI6MDA6MDBaIiwibGFuZ19hbHBoYV8zIjoiZW5nIn19','2020-03-18 16:15:45.919076'),('2k8qwx1ztqtbhhn0of0mbzl3rrsaurur','ODMwMzE5MzhjMzBhNmQ1Y2Y4ODRhODNhMmY2MmNkZjgxZWMzMjk5ODp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJyZXByZXNlbnRhdGlvbnMiOm51bGwsInByb2Nlc3NfaWQiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJtZF9wcm9wZXJ0aWVzIjp7ImNzcmZtaWRkbGV3YXJldG9rZW4iOiJrQWFZdnIxN2ZFYVVDSzRmeGlKYVRBT0xaZFRXMkx5UjlKeFVxSncwRjNFOTI0QW5FbGYybXZrVk5sa1V1dmdWIiwidGl0bGUiOiJ0ZXN0IHRpdGxlIiwiZGVzY3JpcHRpb24iOiJ0ZXN0IGRlc2NyaXB0aW9uIG5lZWRzIHRvIGJlIGV4dGVuZGVkIiwidGFncyI6IltdIiwidXNlcl9nZW5lcmF0ZWRfdGFncyI6IltdIiwiY29udGFjdF9wb2ludCI6IlRlc3Rwcm92aWRlciIsImNvbnRhY3RfZW1haWwiOiJ0ZXN0cHJvdmlkZXJAZWFyay1wcm9qZWN0LmNvbSIsInB1Ymxpc2hlciI6IlRlc3Rwcm92aWRlciIsInB1Ymxpc2hlcl9lbWFpbCI6InRlc3Rwcm92aWRlckBlYXJrLXByb2plY3QuY29tIiwibGFuZ3VhZ2UiOiJFbmdsaXNoIiwiaWRlbnRpZmllciI6ImNkOWU2ZWU4LWRmYjMtNDhjNC04MzRjLTg1ZDFjZmI3MDdiOSIsImN1cnJkYXRlIjoiMjAyMC0wMy0wNlQxNTo1MTo1MloiLCJkYXRlIjoiMDYuMDMuMjAyMCIsImxhc3RfY2hhbmdlIjoiMjAyMC0wMy0wNlQxNTo1MTo1MloiLCJjcmVhdGVkIjoiMjAyMC0wMy0wNlQxNTo1MTo1MloiLCJkamFuZ29fc2VydmljZV9ob3N0IjoibG9jYWxob3N0IiwiZGphbmdvX3NlcnZpY2VfcG9ydCI6ODAwMCwibGFuZGluZ19wYWdlIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2Vhcmt3ZWIvYWNjZXNzL2RhdGFzZXQvY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5LyIsInJlcHJlc2VudGF0aW9ucyI6eyJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6InBkZiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IlBERiByZXByZXNlbnRhdGlvbiIsImFjY2Vzc19yaWdodHMiOiJmcmVlIiwiZmlsZV9pdGVtcyI6WyJyZXByZXNlbnRhdGlvbnMvZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcS9kYXRhL3RpY2tldHMucGRmIiwicmVwcmVzZW50YXRpb25zL2Ric2huZmR2YnJ3bHFueW50Y29mcWViZWVoaWdob3JsbWtodmF5anEvZGF0YS9iZXN0ZWxsdW5nLXN0cmlja2phY2tlLnBkZiJdfSwibmZ0b2tjbXpicWZ4bHppYWd3Y3V4YmpmcGRsZmRmdmNzb2xvbmZtaCI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJwbmciLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJQTkcgZmlsZXMiLCJhY2Nlc3NfcmlnaHRzIjoiZnJlZSIsImZpbGVfaXRlbXMiOlsicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS90aWNrZXRzLTEucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS90aWNrZXRzLTIucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS90aWNrZXRzLTAucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS9iZXN0ZWxsdW5nLXN0cmlja2phY2tlLTEucG5nIiwicmVwcmVzZW50YXRpb25zL25mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgvZGF0YS9iZXN0ZWxsdW5nLXN0cmlja2phY2tlLTAucG5nIl19LCJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxX21pZy0xIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6IiIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IiIsImFjY2Vzc19yaWdodHMiOiIiLCJmaWxlX2l0ZW1zIjpbXX19LCJub2RlX25hbWVzcGFjZV9pZCI6ImVhcmsiLCJyZXBvX2lkZW50aWZpZXIiOiJpbmZvOmVhcmsvYWl0OnJlcG9zaXRvcnkxIiwicmVwb190aXRsZSI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2Rlc2NyaXB0aW9uIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fY2F0YWxvZ3VlX2lzc3VlZCI6IjIwMjAtMDEtMDFUMTI6MDA6MDBaIiwicmVwb19jYXRhbG9ndWVfbW9kaWZpZWQiOiIyMDIwLTAyLTAxVDEyOjAwOjAwWiIsImxhbmdfYWxwaGFfMyI6ImVuZyJ9fQ==','2020-03-20 14:52:59.321679'),('0of55d3dinja8n47o1chjpijy9yxixbk','NjlmYTU0YWIzYjhjODZlY2M1MDAxNjZmZWViOGViMjg0YzFiOGQ4ZDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwiX2xhbmd1YWdlIjoiZW4iLCJzdGVwMSI6bnVsbCwic3RlcDIiOm51bGwsInJlcHJlc2VudGF0aW9ucyI6bnVsbCwibWRfcHJvcGVydGllcyI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoiOGpBamNDbWN0Z1Y3SGZXdlhuTDFsU1dRWWhYOU9zVk5icHVGR0lrVE53MEJIaHJITUgwRzRXRjRmcEptT25UcyIsInRpdGxlIjoidGVzdCB0aXRsZSIsImRlc2NyaXB0aW9uIjoidGVzdCBkZXNjcmlwdGlvbiBuZWVkcyB0byBiZSBleHRlbmRlZCIsInRhZ3MiOiJbXSIsInVzZXJfZ2VuZXJhdGVkX3RhZ3MiOiJbXSIsImNvbnRhY3RfcG9pbnQiOiJUZXN0cHJvdmlkZXIiLCJjb250YWN0X2VtYWlsIjoidGVzdHByb3ZpZGVyQGVhcmstcHJvamVjdC5jb20iLCJwdWJsaXNoZXIiOiJUZXN0cHJvdmlkZXIiLCJwdWJsaXNoZXJfZW1haWwiOiJ0ZXN0cHJvdmlkZXJAZWFyay1wcm9qZWN0LmNvbSIsImxhbmd1YWdlIjoiRW5nbGlzaCIsImlkZW50aWZpZXIiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJjdXJyZGF0ZSI6IjIwMjAtMDMtMDlUMDg6NDU6NDhaIiwiZGF0ZSI6IjA5LjAzLjIwMjAiLCJsYXN0X2NoYW5nZSI6IjIwMjAtMDMtMDlUMDg6NDU6NDhaIiwiY3JlYXRlZCI6IjIwMjAtMDMtMDlUMDg6NDU6NDhaIiwiZGphbmdvX3NlcnZpY2VfaG9zdCI6ImxvY2FsaG9zdCIsImRqYW5nb19zZXJ2aWNlX3BvcnQiOjgwMDAsImxhbmRpbmdfcGFnZSI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC9lYXJrd2ViL2FjY2Vzcy9kYXRhc2V0L2NkOWU2ZWU4LWRmYjMtNDhjNC04MzRjLTg1ZDFjZmI3MDdiOS8iLCJyZXByZXNlbnRhdGlvbnMiOnsiZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcSI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJwZGYiLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJQREYgcmVwcmVzZW50YXRpb24iLCJhY2Nlc3NfcmlnaHRzIjoiZnJlZSIsImZpbGVfaXRlbXMiOlsicmVwcmVzZW50YXRpb25zL2Ric2huZmR2YnJ3bHFueW50Y29mcWViZWVoaWdob3JsbWtodmF5anEvZGF0YS90aWNrZXRzLnBkZiIsInJlcHJlc2VudGF0aW9ucy9kYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxL2RhdGEvYmVzdGVsbHVuZy1zdHJpY2tqYWNrZS5wZGYiXX0sIm5mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoicG5nIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiUE5HIGZpbGVzIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUiLCJmaWxlX2l0ZW1zIjpbInJlcHJlc2VudGF0aW9ucy9uZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oL2RhdGEvdGlja2V0cy0xLnBuZyIsInJlcHJlc2VudGF0aW9ucy9uZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oL2RhdGEvdGlja2V0cy0yLnBuZyIsInJlcHJlc2VudGF0aW9ucy9uZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oL2RhdGEvdGlja2V0cy0wLnBuZyIsInJlcHJlc2VudGF0aW9ucy9uZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oL2RhdGEvYmVzdGVsbHVuZy1zdHJpY2tqYWNrZS0xLnBuZyIsInJlcHJlc2VudGF0aW9ucy9uZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oL2RhdGEvYmVzdGVsbHVuZy1zdHJpY2tqYWNrZS0wLnBuZyJdfX0sIm5vZGVfbmFtZXNwYWNlX2lkIjoiZWFyayIsInJlcG9faWRlbnRpZmllciI6ImluZm86ZWFyay9haXQ6cmVwb3NpdG9yeTEiLCJyZXBvX3RpdGxlIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fZGVzY3JpcHRpb24iOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19jYXRhbG9ndWVfaXNzdWVkIjoiMjAyMC0wMS0wMVQxMjowMDowMFoiLCJyZXBvX2NhdGFsb2d1ZV9tb2RpZmllZCI6IjIwMjAtMDItMDFUMTI6MDA6MDBaIiwibGFuZ19hbHBoYV8zIjoiZW5nIn0sImlkZW50aWZpZXIiOiJlYXJrOmNtY2hmYnN1cmVqbXJmeWpldmhjc2ZoeGluYWlqd3huam1waXhyemwiLCJwcm9jZXNzX2lkIjoiY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5In0=','2020-03-23 08:13:54.819420'),('3a7ce986iaredsh9u42lsu9abvkg84j2','MTZkOTZjOTdlYWY4MGFkNjY4ZTUzMDA1ZjMxYWQwNWM1YjBmYzMzMDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwic3RlcDEiOm51bGwsInN0ZXAyIjpudWxsLCJpZGVudGlmaWVyIjoiZWFyazpjbWNoZmJzdXJlam1yZnlqZXZoY3NmaHhpbmFpand4bmptcGl4cnpsIiwicmVwcmVzZW50YXRpb25zIjpudWxsLCJwcm9jZXNzX2lkIjoiY2Q5ZTZlZTgtZGZiMy00OGM0LTgzNGMtODVkMWNmYjcwN2I5IiwibWRfcHJvcGVydGllcyI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoiMkU1N1h2Z3FtZmxEMjRySW1iZVJqMndXUmM0S0Z6dFZxQWhYejdKVDNiUEYyYzN6cGhjV0JBMVRDekxUU3hIVyIsInRpdGxlIjoidGVzdCB0aXRsZSIsImRlc2NyaXB0aW9uIjoidGVzdCBkZXNjcmlwdGlvbiBuZWVkcyB0byBiZSBleHRlbmRlZCIsInRhZ3MiOiJbXSIsInVzZXJfZ2VuZXJhdGVkX3RhZ3MiOiJbXSIsImNvbnRhY3RfcG9pbnQiOiJUZXN0cHJvdmlkZXIiLCJjb250YWN0X2VtYWlsIjoidGVzdHByb3ZpZGVyQGVhcmstcHJvamVjdC5jb20iLCJwdWJsaXNoZXIiOiJUZXN0cHJvdmlkZXIiLCJwdWJsaXNoZXJfZW1haWwiOiJ0ZXN0cHJvdmlkZXJAZWFyay1wcm9qZWN0LmNvbSIsImxhbmd1YWdlIjoiRW5nbGlzaCIsImlkZW50aWZpZXIiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJjdXJyZGF0ZSI6IjIwMjAtMDMtMTJUMDk6MzI6MjNaIiwiZGF0ZSI6IjEyLjAzLjIwMjAiLCJsYXN0X2NoYW5nZSI6IjIwMjAtMDMtMTJUMDk6MzI6MjNaIiwiY3JlYXRlZCI6IjIwMjAtMDMtMTJUMDk6MzI6MjNaIiwiZGphbmdvX3NlcnZpY2VfaG9zdCI6ImxvY2FsaG9zdCIsImRqYW5nb19zZXJ2aWNlX3BvcnQiOjgwMDAsImxhbmRpbmdfcGFnZSI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC9lYXJrd2ViL2FjY2Vzcy9kYXRhc2V0L2NkOWU2ZWU4LWRmYjMtNDhjNC04MzRjLTg1ZDFjZmI3MDdiOS8iLCJyZXByZXNlbnRhdGlvbnMiOnsiZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcSI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJqcGciLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJKUEVHIGltYWdlIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUiLCJmaWxlX2l0ZW1zIjpbInJlcHJlc2VudGF0aW9ucy9kYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxL2RhdGEvQkRfMDM1NV9TMS5qcGciXX0sIm5mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoicG5nIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiUE5HIGltYWdlIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUiLCJmaWxlX2l0ZW1zIjpbInJlcHJlc2VudGF0aW9ucy9uZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oL2RhdGEvQkRfMDM1NV9TMS5wbmciXX19LCJub2RlX25hbWVzcGFjZV9pZCI6ImVhcmsiLCJyZXBvX2lkZW50aWZpZXIiOiJpbmZvOmVhcmsvYWl0OnJlcG9zaXRvcnkxIiwicmVwb190aXRsZSI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2Rlc2NyaXB0aW9uIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fY2F0YWxvZ3VlX2lzc3VlZCI6IjIwMjAtMDEtMDFUMTI6MDA6MDBaIiwicmVwb19jYXRhbG9ndWVfbW9kaWZpZWQiOiIyMDIwLTAyLTAxVDEyOjAwOjAwWiIsImxhbmdfYWxwaGFfMyI6ImVuZyJ9fQ==','2020-03-26 08:47:46.137223'),('g6cr633naaqtaz8mas40zw82obys7hfq','ODkyMmI0OWU3M2YxYjU4M2Y1Mjc3ZjNhYTdmYzMxNDdjMTJiMmRjZDp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwiX2xhbmd1YWdlIjoiZW4iLCJzdGVwMSI6bnVsbCwic3RlcDIiOm51bGwsInJlcHJlc2VudGF0aW9ucyI6bnVsbCwibWRfcHJvcGVydGllcyI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoiY1FObjBIeVhKT1ZvWHZnTllabE9La05TcnNNTFpXdXlHWmhkS2xnN01zZHB0aFE0ZnVNRlRmaEk4dERlc1FhbSIsInRpdGxlIjoiTW96YXJ0OiBCcmllZiwgendpc2NoZW4gMTc3Ny0xMC0yMyB1bmQgMTc3Ny0xMC0yNSIsImRlc2NyaXB0aW9uIjoiTW96YXJ0OiAgQnJpZWYsIHp3aXNjaGVuIDE3NzctMTAtMjMgdW5kIDE3NzctMTAtMjUiLCJ0YWdzIjoiW10iLCJ1c2VyX2dlbmVyYXRlZF90YWdzIjoiW10iLCJjb250YWN0X3BvaW50IjoiU2FsemJ1cmcgKEFUKSwgSW50ZXJuYXRpb25hbGUgU3RpZnR1bmcgTW96YXJ0ZXVtIiwiY29udGFjdF9lbWFpbCI6ImNvbnRhY3RAZG1lLm1vemFydGV1bS5hdCIsInB1Ymxpc2hlciI6IlNhbHpidXJnIChBVCksIEludGVybmF0aW9uYWxlIFN0aWZ0dW5nIE1vemFydGV1bSIsInB1Ymxpc2hlcl9lbWFpbCI6ImNvbnRhY3RAZG1lLm1vemFydGV1bS5hdCIsImxhbmd1YWdlIjoiRW5nbGlzaCIsImlkZW50aWZpZXIiOiJjZDllNmVlOC1kZmIzLTQ4YzQtODM0Yy04NWQxY2ZiNzA3YjkiLCJjdXJyZGF0ZSI6IjIwMjAtMDMtMTJUMTA6NTg6MzRaIiwiZGF0ZSI6IjEyLjAzLjIwMjAiLCJsYXN0X2NoYW5nZSI6IjIwMjAtMDMtMTJUMTA6NTg6MzRaIiwiY3JlYXRlZCI6IjIwMjAtMDMtMTJUMTA6NTg6MzRaIiwiZGphbmdvX3NlcnZpY2VfaG9zdCI6ImxvY2FsaG9zdCIsImRqYW5nb19zZXJ2aWNlX3BvcnQiOjgwMDAsImxhbmRpbmdfcGFnZSI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODAwMC9lYXJrd2ViL2FjY2Vzcy9kYXRhc2V0L2NkOWU2ZWU4LWRmYjMtNDhjNC04MzRjLTg1ZDFjZmI3MDdiOS8iLCJyZXByZXNlbnRhdGlvbnMiOnsiZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcSI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJqcGciLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJKUEVHIGltYWdlIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUiLCJmaWxlX2l0ZW1zIjpbInJlcHJlc2VudGF0aW9ucy9kYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxL2RhdGEvQkRfMDM1NV9TMS5qcGciXX0sIm5mdG9rY216YnFmeGx6aWFnd2N1eGJqZnBkbGZkZnZjc29sb25mbWgiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoicG5nIiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiUE5HIGltYWdlIiwiYWNjZXNzX3JpZ2h0cyI6ImZyZWUiLCJmaWxlX2l0ZW1zIjpbInJlcHJlc2VudGF0aW9ucy9uZnRva2NtemJxZnhsemlhZ3djdXhiamZwZGxmZGZ2Y3NvbG9uZm1oL2RhdGEvQkRfMDM1NV9TMS5wbmciXX0sImJ0dnZhcndydmhtamVhc2VwemFydHlwc2ptZXhhaWd1cXllaXJ4ZWIiOnsiZGlzdHJpYnV0aW9uX2xhYmVsIjoidHh0IiwiZGlzdHJpYnV0aW9uX2Rlc2NyaXB0aW9uIjoiVHJhbnNjcmlwdGlvbiIsImFjY2Vzc19yaWdodHMiOiJmcmVlIiwiZmlsZV9pdGVtcyI6WyJyZXByZXNlbnRhdGlvbnMvYnR2dmFyd3J2aG1qZWFzZXB6YXJ0eXBzam1leGFpZ3VxeWVpcnhlYi9kYXRhL3RyYW5zY3JpcHRpb24udHh0Il19fSwibm9kZV9uYW1lc3BhY2VfaWQiOiJlYXJrIiwicmVwb19pZGVudGlmaWVyIjoiaW5mbzplYXJrL2FpdDpyZXBvc2l0b3J5MSIsInJlcG9fdGl0bGUiOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19kZXNjcmlwdGlvbiI6IkUtQVJLIFJlcG9zaXRvcnkiLCJyZXBvX2NhdGFsb2d1ZV9pc3N1ZWQiOiIyMDIwLTAxLTAxVDEyOjAwOjAwWiIsInJlcG9fY2F0YWxvZ3VlX21vZGlmaWVkIjoiMjAyMC0wMi0wMVQxMjowMDowMFoiLCJsYW5nX2FscGhhXzMiOiJlbmcifX0=','2020-03-26 10:04:30.334546'),('uo54zdmwgh2laqrsfc7hl2cx9dhm8asd','ZmZjYjU1MmFjOTQ2ODg4N2VhMzA1ZWZiNDU1MDU2ODEyNTQxYmU1OTp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwicHJvY2Vzc19pZCI6IjdhZDc1MTI3LTQ5OTgtNDI5OS1hNjcwLWY2ODA2NDJiZTY5ZSIsInN0ZXAxIjp7ImNzcmZtaWRkbGV3YXJldG9rZW4iOiI1amI1dGplcnFNYll1elVueks4dzkwU3FveTkxZEpSMmtBcEhSMGwwNkRqTHRTT3I1QTVpRUhmcXA5RGtpVUNxIiwidGl0bGUiOiJFeGFtcGxlIG9mIGdlb2dyYXBoaWMgZGF0YSIsImRlc2NyaXB0aW9uIjoiRXhhbXBsZSBvZiBnZW9ncmFwaGljIGRhdGEiLCJ0YWdzIjoiW10iLCJ1c2VyX2dlbmVyYXRlZF90YWdzIjoiW10ifSwic3RlcDIiOnsiY3NyZm1pZGRsZXdhcmV0b2tlbiI6IkI2WlpDOXFPNENCbTBtNTV6Q0hZTVlTaUgxN2wyeERKUW5kQjBReG5LdEo5WkZaOTVzRUtoRmZpSUNCRTdJbzciLCJjb250YWN0X3BvaW50IjoiTWluaXN0cnkgb2YgQ3VsdHVyZSBTbG92ZW5pYSAoRXhhbXBsZSkiLCJjb250YWN0X2VtYWlsIjoiZ3AubWtAZ292LnNpIiwicHVibGlzaGVyIjoiTWluaXN0cnkgb2YgQ3VsdHVyZSBTbG92ZW5pYSAoRXhhbXBsZSkiLCJwdWJsaXNoZXJfZW1haWwiOiJncC5ta0Bnb3Yuc2kiLCJsYW5ndWFnZSI6IkVuZ2xpc2gifX0=','2020-03-31 10:27:25.495957'),('t8on34pymiqv78guh420ize1uij95m7m','NTVlMjZhNzA3MGE3YTE3MTk1Y2FlYzJhMGJhNDJlMmNkMDhhYTBmZTp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIiwic3RlcDEiOnsiY3NyZm1pZGRsZXdhcmV0b2tlbiI6ImtweEFORDl6ZGZRRTFua080bDc2NWMwZlZGOVhuN0FBUDJSaGk5eVhtaWl1Z29LU0IwU2dnU2k0VkxSY3BYV0siLCJ0aXRsZSI6IkxldHRlciB0byBKZXJlbXkgQmVudGhhbSIsImRlc2NyaXB0aW9uIjoiRGF0ZV8xIDE3ODktMDUtMjJcclxuXHJcbkJveCA1NDFcclxuXHJcbkZvbGlvIG51bWJlciAwNTNcclxuXHJcbkltYWdlIDAwMVxyXG5cclxuQ2F0ZWdvcnkgQ29ycmVzcG9uZGVuY2VcclxuXHJcblBlbm5lciBcIldpbGxpYW0gUGV0dHksIDJuZCBFYXJsIFNoZWxidXJuZSwgTG9yZCBMYW5zZG93bmVcIiIsInRhZ3MiOiJbXSIsInVzZXJfZ2VuZXJhdGVkX3RhZ3MiOiJbXSJ9LCJzdGVwMiI6eyJjc3JmbWlkZGxld2FyZXRva2VuIjoidWJMZXU4ZU1KTTd1UjJUa0RtM2syZ1RleGc0SXJ5SXdaTzVWWkVEYVNQems2M2pvYTFPdWRXYjN4bU1YdG80RyIsImNvbnRhY3RfcG9pbnQiOiJUaGUgQmVudGhhbSBQcm9qZWN0IiwiY29udGFjdF9lbWFpbCI6InRyYW5zY3JpYmUuYmVudGhhbUB1Y2wuYWMudWsiLCJwdWJsaXNoZXIiOiJGYWN1bHR5IG9mIExhd3MsIFVuaXZlcnNpdHkgQ29sbGVnZSBMb25kb24iLCJwdWJsaXNoZXJfZW1haWwiOiJ0cmFuc2NyaWJlLmJlbnRoYW1AdWNsLmFjLnVrIiwibGFuZ3VhZ2UiOiJFbmdsaXNoIn0sInJlcHJlc2VudGF0aW9ucyI6bnVsbCwiX2xhbmd1YWdlIjoiZW4iLCJwcm9jZXNzX2lkIjoiNDA3OWZhYjEtNTRhOS00Njg0LWJlOWEtOWVmNDA4ZDBkODJhIiwiaWRlbnRpZmllciI6InVybjp1dWlkOmFmN2MwYTY0LTAxYjUtNDcxNC05ZjhmLTkwYjI0OTNkYTk0ZiIsIm1kX3Byb3BlcnRpZXMiOnsiY3NyZm1pZGRsZXdhcmV0b2tlbiI6ImNKcmNwMU5iblRkOTJKdDBxOW5wcVFZbU5yOEl2SUhvSG1MVFV4Y3p3V0ZaaEtUNFhPOHpCd2diTnhRWHh5M3kiLCJ0aXRsZSI6IkxldHRlciB0byBKZXJlbXkgQmVudGhhbSIsImRlc2NyaXB0aW9uIjoiRGF0ZV8xIDE3ODktMDUtMjJcclxuXHJcbkJveCA1NDFcclxuXHJcbkZvbGlvIG51bWJlciAwNTNcclxuXHJcbkltYWdlIDAwMVxyXG5cclxuQ2F0ZWdvcnkgQ29ycmVzcG9uZGVuY2VcclxuXHJcblBlbm5lciBcIldpbGxpYW0gUGV0dHksIDJuZCBFYXJsIFNoZWxidXJuZSwgTG9yZCBMYW5zZG93bmVcIiIsInRhZ3MiOiJbXSIsInVzZXJfZ2VuZXJhdGVkX3RhZ3MiOiJbXSIsImNvbnRhY3RfcG9pbnQiOiJUaGUgQmVudGhhbSBQcm9qZWN0IiwiY29udGFjdF9lbWFpbCI6InRyYW5zY3JpYmUuYmVudGhhbUB1Y2wuYWMudWsiLCJwdWJsaXNoZXIiOiJGYWN1bHR5IG9mIExhd3MsIFVuaXZlcnNpdHkgQ29sbGVnZSBMb25kb24iLCJwdWJsaXNoZXJfZW1haWwiOiJ0cmFuc2NyaWJlLmJlbnRoYW1AdWNsLmFjLnVrIiwibGFuZ3VhZ2UiOiJFbmdsaXNoIiwiaWRlbnRpZmllciI6IjhmOGY4YTI2LTA2N2QtNGZiMi1hM2ZkLTdlZDY2MTRhMTQzMSIsImN1cnJkYXRlIjoiMjAyMC0wMy0xM1QxNDoyMjozNFoiLCJkYXRlIjoiMTMuMDMuMjAyMCIsImxhc3RfY2hhbmdlIjoiMjAyMC0wMy0xM1QxNDoyMjozNFoiLCJjcmVhdGVkIjoiMjAyMC0wMy0xM1QxNDoyMjozNFoiLCJkamFuZ29fc2VydmljZV9ob3N0IjoibG9jYWxob3N0IiwiZGphbmdvX3NlcnZpY2VfcG9ydCI6ODAwMCwibGFuZGluZ19wYWdlIjoiaHR0cDovL2xvY2FsaG9zdDo4MDAwL2Vhcmt3ZWIvYWNjZXNzL3BhY2thZ2UvOGY4ZjhhMjYtMDY3ZC00ZmIyLWEzZmQtN2VkNjYxNGExNDMxLyIsInJlcHJlc2VudGF0aW9ucyI6eyJkYnNobmZkdmJyd2xxbnludGNvZnFlYmVlaGlnaG9ybG1raHZheWpxIjp7ImRpc3RyaWJ1dGlvbl9sYWJlbCI6InBuZyIsImRpc3RyaWJ1dGlvbl9kZXNjcmlwdGlvbiI6IlBORyBpbWFnZSIsImFjY2Vzc19yaWdodHMiOiJmcmVlIiwiZmlsZV9pdGVtcyI6WyJyZXByZXNlbnRhdGlvbnMvZGJzaG5mZHZicndscW55bnRjb2ZxZWJlZWhpZ2hvcmxta2h2YXlqcS9kYXRhL2plcmVteV9iZW50aGFtX2piXzU0MV8wNTNfMDAxLnBuZyJdfSwiYnR2dmFyd3J2aG1qZWFzZXB6YXJ0eXBzam1leGFpZ3VxeWVpcnhlYiI6eyJkaXN0cmlidXRpb25fbGFiZWwiOiJ0eHQiLCJkaXN0cmlidXRpb25fZGVzY3JpcHRpb24iOiJUWFQgVHJhbnNjcmlwdGlvbiIsImFjY2Vzc19yaWdodHMiOiJmcmVlIiwiZmlsZV9pdGVtcyI6WyJyZXByZXNlbnRhdGlvbnMvYnR2dmFyd3J2aG1qZWFzZXB6YXJ0eXBzam1leGFpZ3VxeWVpcnhlYi9kYXRhL2plcmVteV9iZW50aGFtX2piXzU0MV8wNTNfMDAxLnR4dCJdfX0sIm5vZGVfbmFtZXNwYWNlX2lkIjoiZWFyayIsInJlcG9faWRlbnRpZmllciI6ImluZm86ZWFyay9haXQ6cmVwb3NpdG9yeTEiLCJyZXBvX3RpdGxlIjoiRS1BUksgUmVwb3NpdG9yeSIsInJlcG9fZGVzY3JpcHRpb24iOiJFLUFSSyBSZXBvc2l0b3J5IiwicmVwb19jYXRhbG9ndWVfaXNzdWVkIjoiMjAyMC0wMS0wMVQxMjowMDowMFoiLCJyZXBvX2NhdGFsb2d1ZV9tb2RpZmllZCI6IjIwMjAtMDItMDFUMTI6MDA6MDBaIiwibGFuZ19hbHBoYV8zIjoiZW5nIn19','2020-03-27 15:00:36.621873'),('1e9ool5ru3ypaph88nrdenoiy8fsl119','N2JiODZhNjJkYWRmYThkNmZhMzA0MmZkZjFlYzY0YjI2YjM3YzBkOTp7Il9hdXRoX3VzZXJfaWQiOiIxIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI4ZTM0YzcyZmFhMDliOTM1ZTY1YzJkOTI0MmQ1OTMyMTM0MDdlOTNlIn0=','2020-03-31 10:42:17.921188');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `earkuser`
--

DROP TABLE IF EXISTS `earkuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `earkuser` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `org_nsid` varchar(100) NOT NULL,
  `confirmed` tinyint(1) NOT NULL,
  `confirmation_status` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `earkuser`
--

LOCK TABLES `earkuser` WRITE;
/*!40000 ALTER TABLE `earkuser` DISABLE KEYS */;
/*!40000 ALTER TABLE `earkuser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `earkweb_uploadedfile`
--

DROP TABLE IF EXISTS `earkweb_uploadedfile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `earkweb_uploadedfile` (
  `creation_datetime` datetime(6) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(100) NOT NULL,
  `file` varchar(200) NOT NULL,
  `sha256` varchar(64) NOT NULL,
  `creator_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `earkweb_uploadedfile_sha256_a31cc7f5` (`sha256`),
  KEY `earkweb_uploadedfile_creator_id_986d9c8b` (`creator_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `earkweb_uploadedfile`
--

LOCK TABLES `earkweb_uploadedfile` WRITE;
/*!40000 ALTER TABLE `earkweb_uploadedfile` DISABLE KEYS */;
/*!40000 ALTER TABLE `earkweb_uploadedfile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `informationpackage`
--

DROP TABLE IF EXISTS `informationpackage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `informationpackage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `process_id` varchar(200) NOT NULL,
  `package_name` varchar(200) NOT NULL,
  `identifier` varchar(200) NOT NULL,
  `external_id` varchar(200) NOT NULL,
  `parent_id` varchar(200) NOT NULL,
  `version` int(11) NOT NULL,
  `work_dir` varchar(4096) NOT NULL,
  `storage_dir` varchar(4096) NOT NULL,
  `basic_metadata` longtext,
  `last_change` datetime(6) NOT NULL,
  `created` datetime(6) NOT NULL,
  `deleted` tinyint(1) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `informationpackage_user_id_092cb923` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=79 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `informationpackage`
--

LOCK TABLES `informationpackage` WRITE;
/*!40000 ALTER TABLE `informationpackage` DISABLE KEYS */;
INSERT INTO `informationpackage` VALUES (15,'21a45eaf-fcb0-4cf7-92bf-5747562cf60a','example.airtravel','','','',0,'/var/data/repo/work/21a45eaf-fcb0-4cf7-92bf-5747562cf60a','',NULL,'2020-03-27 10:23:52.779923','2020-03-27 10:23:52.779999',0,1),(16,'7f76c1fe-df10-499d-ad78-c5d93e106bd8','example.biostats','urn:uuid:ca15f864-9421-40bd-b4f4-f5b4a0f9f658','https://people.sc.fsu.edu/~jburkardt/data/csv/biostats.csv','',1,'/var/data/repo/work/7f76c1fe-df10-499d-ad78-c5d93e106bd8','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+c/a1/5f/86/4-/94/21/-4/0b/d-/b4/f4/-f/5b/4a/0f/9f/65/8/data/00001/urn+uuid+ca15f864-9421-40bd-b4f4-f5b4a0f9f658','{\n    \"title\": \"Biometric statistics for a group of office workers\",\n    \"description\": \"Biometric statistics for a group of office workers. \\r\\nThere are 18 records, recording Name, Sex, Age, Height, Weight.\\r\\nThere is an initial header line. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"7f76c1fe-df10-499d-ad78-c5d93e106bd8\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T10:49:26Z\",\n    \"created\": \"2020-03-27T10:49:26Z\",\n    \"representations\": {\n        \"a40d0d9d-4c1c-42b2-ac33-a4062d549e59\": {\n            \"distribution_label\": \"\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/a40d0d9d-4c1c-42b2-ac33-a4062d549e59/data/biostats.csv\"\n            ]\n        },\n        \"bcd6b692-ce4c-4019-b667-698cabf7e670\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open document spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/bcd6b692-ce4c-4019-b667-698cabf7e670/data/biostats.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 10:49:45.000000','2020-03-27 10:31:55.805131',0,1),(14,'921858c4-43e5-49a3-b459-94fe300174d0','example.addresses','urn:uuid:ac11fb1e-b4d9-4e6f-a2be-ba2d2987bfa2','','',3,'/var/data/repo/work/921858c4-43e5-49a3-b459-94fe300174d0','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+a/c1/1f/b1/e-/b4/d9/-4/e6/f-/a2/be/-b/a2/d2/98/7b/fa/2/data/00003/urn+uuid+ac11fb1e-b4d9-4e6f-a2be-ba2d2987bfa2','{\n    \"title\": \"Address table with 6 records\",\n    \"description\": \"An example file with 6 records of addresses structured in 6 fields. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"921858c4-43e5-49a3-b459-94fe300174d0\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T10:07:36Z\",\n    \"created\": \"2020-03-27T10:07:36Z\",\n    \"representations\": {\n        \"dd19e390-ae51-4a82-92c9-6e5c4ca381df\": {\n            \"distribution_label\": \"spreadsheet\",\n            \"distribution_description\": \"ODF spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/dd19e390-ae51-4a82-92c9-6e5c4ca381df/data/addresses.ods\"\n            ]\n        },\n        \"76641c03-eded-479d-94d4-13dbde276f86\": {\n            \"distribution_label\": \"csv\",\n            \"distribution_description\": \"CSV table\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/76641c03-eded-479d-94d4-13dbde276f86/data/addresses.csv\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 10:10:36.000000','2020-03-26 21:57:33.823910',0,1),(17,'cd81f30a-2a66-4c8d-9f3d-54464aa9f131','example.cities','urn:uuid:a69858fd-0517-4348-b620-94f72777c372','https://people.sc.fsu.edu/~jburkardt/data/csv/cities.csv','',1,'/var/data/repo/work/cd81f30a-2a66-4c8d-9f3d-54464aa9f131','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+a/69/85/8f/d-/05/17/-4/34/8-/b6/20/-9/4f/72/77/7c/37/2/data/00001/urn+uuid+a69858fd-0517-4348-b620-94f72777c372','{\n    \"title\": \"Cities records\",\n    \"description\": \"An example file with 128 records. \\r\\nThere are 10 fields. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"cd81f30a-2a66-4c8d-9f3d-54464aa9f131\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T10:55:50Z\",\n    \"created\": \"2020-03-27T10:55:50Z\",\n    \"representations\": {\n        \"cc3bc73e-27da-46ac-b132-9ca30e5dcb13\": {\n            \"distribution_label\": \"\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/cc3bc73e-27da-46ac-b132-9ca30e5dcb13/data/cities.csv\"\n            ]\n        },\n        \"efe90ff9-ba4d-4ef7-879a-738154982144\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open Document Spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/efe90ff9-ba4d-4ef7-879a-738154982144/data/cities.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 10:56:20.000000','2020-03-27 10:50:46.064264',0,1),(19,'7d7055c1-dcdb-43a0-86ec-0fbb73794094','examples.crash_catalonia','urn:uuid:80a905d5-1468-473c-a8ca-31bfa3a2ea6c','https://people.sc.fsu.edu/~jburkardt/data/csv/crash_catalonia.csv','',1,'/var/data/repo/work/7d7055c1-dcdb-43a0-86ec-0fbb73794094','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+8/0a/90/5d/5-/14/68/-4/73/c-/a8/ca/-3/1b/fa/3a/2e/a6/c/data/00001/urn+uuid+80a905d5-1468-473c-a8ca-31bfa3a2ea6c','{\n    \"title\": \"Number of car crashes in Catalonia from 2000 to 2011\",\n    \"description\": \"Number of car crashes in Catalonia from 2000 to 2011, by day of week. \\r\\nThere are 7 records, with two values each. \\r\\nThere is also an initial header line. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"7d7055c1-dcdb-43a0-86ec-0fbb73794094\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T11:12:19Z\",\n    \"created\": \"2020-03-27T11:12:19Z\",\n    \"representations\": {\n        \"6f7474e7-93d5-4c61-9970-ad11760e6060\": {\n            \"distribution_label\": \"\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/6f7474e7-93d5-4c61-9970-ad11760e6060/data/crash_catalonia.csv\"\n            ]\n        },\n        \"5798b9ad-2827-4849-ba66-e8ed2b10c5db\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open document spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/5798b9ad-2827-4849-ba66-e8ed2b10c5db/data/crash_catalonia.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 11:12:35.000000','2020-03-27 11:09:30.484712',0,1),(20,'b2c0a6d7-f042-47ec-b232-2a824a1966b2','examples.deniro','urn:uuid:28553e60-b491-43e9-877e-475aade17e11','https://people.sc.fsu.edu/~jburkardt/data/csv/deniro.csv','',1,'/var/data/repo/work/b2c0a6d7-f042-47ec-b232-2a824a1966b2','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+2/85/53/e6/0-/b4/91/-4/3e/9-/87/7e/-4/75/aa/de/17/e1/1/data/00001/urn+uuid+28553e60-b491-43e9-877e-475aade17e11','{\n    \"title\": \"Rotten Tomato ratings of movies with Robert De Niro\",\n    \"description\": \"Rotten Tomato ratings of movies with Robert De Niro. \\r\\nThere are 87 records. Each record has Year, Rating, \\r\\nTitle. There is also an initial header line. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"b2c0a6d7-f042-47ec-b232-2a824a1966b2\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T11:23:06Z\",\n    \"created\": \"2020-03-27T11:23:06Z\",\n    \"representations\": {\n        \"75f2ee87-67f2-480a-9c2d-dc437189469b\": {\n            \"distribution_label\": \"csv\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/75f2ee87-67f2-480a-9c2d-dc437189469b/data/deniro.csv\"\n            ]\n        },\n        \"a4571ffb-e3a6-4a06-b592-710a1667176b\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open document spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/a4571ffb-e3a6-4a06-b592-710a1667176b/data/deniro.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 11:23:21.000000','2020-03-27 11:14:59.265890',0,1),(21,'afceedd1-e6b6-40d3-be25-9315c83c921a','examples.ford_escort','urn:uuid:c9a35773-53b6-461b-bff0-2f201bbb6df1','https://people.sc.fsu.edu/~jburkardt/data/csv/ford_escort.csv','',1,'/var/data/repo/work/afceedd1-e6b6-40d3-be25-9315c83c921a','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+c/9a/35/77/3-/53/b6/-4/61/b-/bf/f0/-2/f2/01/bb/b6/df/1/data/00001/urn+uuid+c9a35773-53b6-461b-bff0-2f201bbb6df1','{\n    \"title\": \"Used Ford Escorts for sale\",\n    \"description\": \"Used Ford Escorts for sale. \\r\\nThere are 23 records of year, mileage and price. \\r\\nThere is also an initial header line. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"afceedd1-e6b6-40d3-be25-9315c83c921a\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T11:29:55Z\",\n    \"created\": \"2020-03-27T11:29:55Z\",\n    \"representations\": {\n        \"4e9cb94e-533d-4c51-9e4f-656fbd438c21\": {\n            \"distribution_label\": \"\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/4e9cb94e-533d-4c51-9e4f-656fbd438c21/data/ford_escort.csv\"\n            ]\n        },\n        \"2f3504aa-c894-43f0-899a-57a306173427\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open document spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/2f3504aa-c894-43f0-899a-57a306173427/data/ford_escort.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 11:50:41.000000','2020-03-27 11:28:11.692964',0,1),(22,'9a101878-c83e-486e-9a75-103d79a686c2','examples.faithful','','https://people.sc.fsu.edu/~jburkardt/data/csv/faithful.csv','',0,'/var/data/repo/work/9a101878-c83e-486e-9a75-103d79a686c2','','{\n    \"title\": \"Old Faithful geyser\",\n    \"description\": \"Old Faithful geyser: index, time between eruptions, and length of eruption. \\r\\n272 records, each with three values. \\r\\nThere is also an initial header line. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"9a101878-c83e-486e-9a75-103d79a686c2\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T11:58:25Z\",\n    \"created\": \"2020-03-27T11:58:25Z\",\n    \"representations\": {\n        \"0191e5b8-01aa-4b4b-9d4b-7733bbde3927\": {\n            \"distribution_label\": \"csv\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/0191e5b8-01aa-4b4b-9d4b-7733bbde3927/data/faithful.csv\"\n            ]\n        },\n        \"ac81280f-e708-4a45-be88-7d4d76f6949f\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open document spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/ac81280f-e708-4a45-be88-7d4d76f6949f/data/faithful.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 11:58:26.000000','2020-03-27 11:51:33.848835',0,1),(23,'2a294071-4f4e-420d-9e2b-fc97f058c99f','examples.college_freshman_kgs','urn:uuid:8d6eecf2-ddf5-450a-a54a-4653d5c94fca','https://people.sc.fsu.edu/~jburkardt/data/csv/freshman_kgs.csv','',1,'/var/data/repo/work/2a294071-4f4e-420d-9e2b-fc97f058c99f','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+8/d6/ee/cf/2-/dd/f5/-4/50/a-/a5/4a/-4/65/3d/5c/94/fc/a/data/00001/urn+uuid+8d6eecf2-ddf5-450a-a54a-4653d5c94fca','{\n    \"title\": \"College freshmen weight\",\n    \"description\": \"Sex, September weight (kgs), April weight (kgs), September BMI, April BMI, for 67 college freshmen. \\r\\nThere is also an initial header line. \",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"2a294071-4f4e-420d-9e2b-fc97f058c99f\",\n    \"date\": \"27.03.2020\",\n    \"lastChange\": \"2020-03-27T12:02:58Z\",\n    \"created\": \"2020-03-27T12:02:58Z\",\n    \"representations\": {\n        \"31814e45-15ad-4fbb-8464-1b49f21241a9\": {\n            \"distribution_label\": \"csv\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/31814e45-15ad-4fbb-8464-1b49f21241a9/data/freshman_kgs.csv\"\n            ]\n        },\n        \"55a4acb7-790a-43b5-8698-97c24ea42a70\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open document spreadsheet\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/55a4acb7-790a-43b5-8698-97c24ea42a70/data/freshman_kgs.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Repository\",\n    \"repoDescription\": \"Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-03-27 12:03:09.000000','2020-03-27 12:00:40.456744',0,1),(38,'d90c7efc-cc79-4b3a-8b6a-315e91c472e1','examples.college_freshmen_lbs','','','',0,'/var/data/repo/work/d90c7efc-cc79-4b3a-8b6a-315e91c472e1','','{ \"title\": \"college freshmen lbs\", \"description\": \"Sex, September weight (lbs), April weight (lbs), September BMI, April BMI, for 67 college freshmen. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"4f09fa76-dea8-4606-9c3c-969686647d6f\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"35195a56-21f6-4b9c-99d6-1b13c5c6d51a\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:00:06.632366','2020-03-27 22:00:05.348587',0,1),(39,'8bfa3279-3c4b-49ce-8ef8-6c1f45d511ee','examples.grades','','','',0,'/var/data/repo/work/8bfa3279-3c4b-49ce-8ef8-6c1f45d511ee','','{ \"title\": \"Example 16 records and 9 fields\", \"description\": \"An example file with 16 records and 9 fields: First name, Last Name, SSN, Test1, Test2, Test3, Test4, Final, Grade. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"52faecff-91c4-48cb-a69a-02a4d89fa7be\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"372d15ac-9f72-4428-8aef-798c96e76dd9\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:05:16.005287','2020-03-27 22:05:14.696419',0,1),(40,'3734463c-3b23-4974-9852-eb701c89756f','examples.homes','','','',0,'/var/data/repo/work/3734463c-3b23-4974-9852-eb701c89756f','','{ \"title\": \"Home sale statistics\", \"description\": \"Home sale statistics. Fifty home sales, with selling price, asking price, living space, rooms, bedrooms, bathrooms, age, acreage, taxes. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"8424b652-5f0c-4cee-91a3-70d53e8606ce\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"6bea51dc-81d2-43e7-b8d1-c60c28f3a700\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:06:01.471801','2020-03-27 22:06:00.204178',0,1),(41,'8401d8b6-b16d-4861-a043-80abcb44c05b','examples.hooke','','','',0,'/var/data/repo/work/8401d8b6-b16d-4861-a043-80abcb44c05b','','{ \"title\": \"A spring experiment is carried out twice\", \"description\": \"Hooke\'s Law demo. A spring experiment is carried out twice. Spring 1 and spring 2 are loaded with 0, 1, 2, ..., 9 equal weights and their lengths are measured. Each record contains the index, weight, spring 1 length and spring 2 length. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"3e43e55d-36e8-4ab6-bb6c-f677e9ecf417\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"e0a917fa-ec81-426f-8d71-3047372d1706\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:06:35.444017','2020-03-27 22:06:34.135732',0,1),(43,'ef1a7202-8d59-465a-b7e6-1791279ca1ba','examples.hurricanes','','','',0,'/var/data/repo/work/ef1a7202-8d59-465a-b7e6-1791279ca1ba','','{ \"title\": \"Hurricane and tropical storm counts for 2005-2015\", \"description\": \"hurricane and tropical storm counts for 2005-2015. Each record includes 13 values: month, historical average, counts for 2005 through 2015. Eight records are stored, for months May through Dec. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"3f979c8a-5a73-4dd0-aca4-fb01d82537d2\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"6cafcfdc-d3ec-4297-91b0-d095c918a2c2\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:07:57.100291','2020-03-27 22:07:55.828950',0,1),(44,'7e0f3dc4-ce27-4c96-91b9-a7db14805b4b','examples.hw_200','','','',0,'/var/data/repo/work/7e0f3dc4-ce27-4c96-91b9-a7db14805b4b','','{ \"title\": \"Height and weight for 200 individuals\", \"description\": \"height and weight for 200 individuals Each record includes 3 values: index, height (inches), weight (pounds). There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"be9fe320-c65d-4690-9b7d-fa720b5a0377\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"24ed15b5-34e9-4d26-93df-282611f9f1d6\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:08:43.024546','2020-03-27 22:08:41.766747',0,1),(45,'a12d3653-b243-4feb-a0ed-93bb89b44d34','examples.lead_shot','','','',0,'/var/data/repo/work/a12d3653-b243-4feb-a0ed-93bb89b44d34','','{ \"title\": \"Grade of lead shot\", \"description\": \"For each grade of lead shot, a record lists the grade name, the weight in ounces, weight in grams, diameter in inches, diameter in millimeters, and the number of pellets per ounce. There are 25 records. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"d08f5d7f-abf1-4fab-b48b-01a7ed87a04c\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"d501d352-c4b8-47e4-8925-3d7f42b98221\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:09:51.168298','2020-03-27 22:09:49.852553',0,1),(46,'33c4a63d-8649-4602-8bf6-9bb654bf9002','examples.letter_frequency','','','',0,'/var/data/repo/work/33c4a63d-8649-4602-8bf6-9bb654bf9002','','{ \"title\": \"Frequency and percentage frequency of the 26 letters\", \"description\": \"In a large text, the frequency and percentage frequency of each of the 26 letters of the alphabet was determined. There are 26 records, each with three values. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"5b6c61d9-e4e4-4ace-a3d9-2dafd5141bbf\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"05e680ba-4c28-4e7d-acb4-3ee0ba1d130a\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:10:50.473244','2020-03-27 22:10:49.190519',0,1),(47,'6884d3f4-79a5-4ea8-902d-d4cda7e16788','examples.mlb_players','','','',0,'/var/data/repo/work/6884d3f4-79a5-4ea8-902d-d4cda7e16788','','{ \"title\": \"Major League Baseball Players\", \"description\": \"Major League Baseball Players: Name, Team, Position, height (inches), weight (pounds), age (years). 1034 records, each with six values. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"2b83e573-796d-4132-99ca-a008538cefd5\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"eb01b4ba-9b5e-4f84-b5a7-c7e7e6195a93\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:11:19.663873','2020-03-27 22:11:18.311842',0,1),(48,'33b8a72d-8cfc-4b7b-a49e-bf8b755cfe58','examples.mlb_teams_2012','','','',0,'/var/data/repo/work/33b8a72d-8cfc-4b7b-a49e-bf8b755cfe58','','{ \"title\": \"Major League Baseball 2012 Season\", \"description\": \"Major League Baseball 2012 Season: Team, Payroll(millions), Wins. 30 records, each with 3 values. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"63f020e0-30b6-4541-af30-4487e702adea\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"97e5bb0c-7cef-4662-a529-a175287b8da6\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:11:48.059353','2020-03-27 22:11:46.807607',0,1),(50,'5cb03689-64b0-401a-92ab-f5769af93555','examples.news_decline','','','',0,'/var/data/repo/work/5cb03689-64b0-401a-92ab-f5769af93555','','{ \"title\": \"Average nightly viewship for 6 TV news magazines for 2009-2011\", \"description\": \"average nightly viewship for 6 TV news magazines for 2009-2011. Each record includes 4 values: show name, 2009, 2010, 2011. Six records are stored, for 60 Minutes, 48 Hours Mystery, 20/20, Nightline, Dateline Friday, and Dateline Sunday. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"095cf832-7e4b-42b0-bea9-16d8a1c1dc2f\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"caef54c0-53fd-4f53-acec-48921138b944\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:17:14.303348','2020-03-27 22:17:13.001339',0,1),(51,'9c641800-9628-46b6-ab8c-0dff0cfaf708','examples.nile','','','',0,'/var/data/repo/work/9c641800-9628-46b6-ab8c-0dff0cfaf708','','{ \"title\": \"Nile flood data\", \"description\": \"Nile flood data; 570 records, each with 2 values: year index, maximum height of Nile flood. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"0149e70b-cd00-4a12-828f-fd74e626e23a\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"8db25cea-e649-4ecc-a2d9-fc2ff8e74761\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:17:50.028277','2020-03-27 22:17:48.744205',0,1),(52,'34ffd770-ca02-47b4-9194-d8e005a317ad','examples.oscar_age_male','','','',0,'/var/data/repo/work/34ffd770-ca02-47b4-9194-d8e005a317ad','','{ \"title\": \"age of female Oscar winners\", \"description\": \"age of female Oscar winners; 89 records: index, age, name, movie. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"ac4f2a6e-ec2d-497f-97c1-17bbe12042ba\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"25a6fb71-f571-4d6e-9133-b171b1f50919\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:18:16.391020','2020-03-27 22:18:15.086288',0,1),(53,'02cd7881-1c12-419a-bbdc-5ff50936cd45','examples.snakes_count_10','','','',0,'/var/data/repo/work/02cd7881-1c12-419a-bbdc-5ff50936cd45','','{ \"title\": \"Game length for one-player version of Snakes and Ladders\", \"description\": \"game length for one-player version of Snakes and Ladders, 10 records, each with 2 values: Game Index, Game Length. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"dfc9fdae-d04f-4e66-b39d-ecd9f0e3fae2\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"858b2b69-6537-4018-9a19-38da37210b08\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:19:18.795036','2020-03-27 22:19:17.550142',0,1),(54,'ebf2689e-3b26-408b-bf61-7d9de18dd5c8','examples.snakes_count_100','','','',0,'/var/data/repo/work/ebf2689e-3b26-408b-bf61-7d9de18dd5c8','','{ \"title\": \"Game length for one-player version of Snakes and Ladders 100 records\", \"description\": \"game length for one-player version of Snakes and Ladders, 100 records, each with 2 values: Game Index, Game Length. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"899cd790-1262-4e4a-8075-c887993dc356\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"07f03bf5-2488-45ab-8c89-1fa823b031ee\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:19:59.661998','2020-03-27 22:19:58.404275',0,1),(55,'f394aa62-fdfb-46f6-ab5d-58535193832b','examples.snakes_count_1000','','','',0,'/var/data/repo/work/f394aa62-fdfb-46f6-ab5d-58535193832b','','{ \"title\": \"Game length for one-player version of Snakes and Ladders for 1000\", \"description\": \"game length for one-player version of Snakes and Ladders, 1000 records, each with 2 values: Game Index, Game Length. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"632817da-9006-421b-a7cf-2ce0161acb30\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"31bc0f4e-d18e-444a-a709-32e7645b39f9\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:20:45.476849','2020-03-27 22:20:44.180199',0,1),(56,'a3ca133c-158d-410c-847e-d789fe167ef4','examples.snakes_count_10000','','','',0,'/var/data/repo/work/a3ca133c-158d-410c-847e-d789fe167ef4','','{ \"title\": \"Game length for one-player version of Snakes and Ladders 10000\", \"description\": \"game length for one-player version of Snakes and Ladders, 10000 records, each with 2 values: Game Index, Game Length. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"23d401f5-f081-4bd5-bae7-3e7ca341f18c\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"786cc69d-c573-4e31-b40f-39fe499e8d32\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:21:20.940776','2020-03-27 22:21:19.410239',0,1),(57,'a40b4b50-1831-4c16-97df-568ae2a640dd','examples.tally_cab','','','',0,'/var/data/repo/work/a40b4b50-1831-4c16-97df-568ae2a640dd','','{ \"title\": \"Tallahassee Cab Fares\", \"description\": \"game length for one-player version of Snakes and Ladders, 10000 records, each with 2 values: Game Index, Game Length. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"67dffbce-8f3a-4a2f-9ac6-a72853a11e7a\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"c482a5e9-bf6f-4aa4-a98e-19e35f9d2bd6\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:21:45.801562','2020-03-27 22:21:44.566273',0,1),(58,'ace0171f-b11c-45ca-a701-3a3036e038d1','examples.taxables','','','',0,'/var/data/repo/work/ace0171f-b11c-45ca-a701-3a3036e038d1','','{ \"title\": \"Taxable items\", \"description\": \"Taxable items, 10 records: index, item name, price, tax, price plus tax. There is also an initial header line.\", \"contactPoint\": \"Contact person\", \"contactEmail\": \"contact@email.com\", \"publisher\": \"Publishing organization\", \"publisherEmail\": \"contact@email.com\", \"language\": \"English\", \"representations\": { \"db9eba49-90eb-4dc5-89c1-abdf2b151cbb\": { \"distribution_label\": \"csv\", \"distribution_description\": \"CSV file\", \"access_rights\": \"free\" }, \"8c03b8fc-ae20-4662-82fa-aef08a647eca\": { \"distribution_label\": \"ods\", \"distribution_description\": \"Open Document Spreadsheet file\", \"access_rights\": \"free\" } } }\n','2020-03-27 22:22:21.201158','2020-03-27 22:22:19.905712',0,1),(59,'975ee2cc-fe3e-46d1-b123-69495233eb5e','examples.trees','urn:uuid:3eed06d5-c302-401f-b787-4292b2b980c4','','',1,'/var/data/repo/work/975ee2cc-fe3e-46d1-b123-69495233eb5e','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+3/ee/d0/6d/5-/c3/02/-4/01/f-/b7/87/-4/29/2b/2b/98/0c/4/data/00001/urn+uuid+3eed06d5-c302-401f-b787-4292b2b980c4','{\n    \"title\": \"Tree measurements\",\n    \"description\": \"Tree measurements, 31 records: index, circumference (in), height (ft), volume (ft^3). There is also an initial header line.\",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"975ee2cc-fe3e-46d1-b123-69495233eb5e\",\n    \"date\": \"07.04.2020\",\n    \"lastChange\": \"2020-04-07T17:12:51Z\",\n    \"created\": \"2020-04-07T17:12:51Z\",\n    \"representations\": {\n        \"7a02beab-447a-4598-8781-352a95811a4c\": {\n            \"distribution_label\": \"csv\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/7a02beab-447a-4598-8781-352a95811a4c/data/trees.csv\"\n            ]\n        },\n        \"521f93ea-96f0-441e-af6d-0f1b362e8179\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open Document Spreadsheet file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/521f93ea-96f0-441e-af6d-0f1b362e8179/data/trees.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Conduit\",\n    \"repoDescription\": \"Data Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-04-07 17:13:01.000000','2020-03-27 22:22:39.230555',0,1),(60,'535448cf-b6ff-4bb2-886f-ee81d05d517f','examples.zillow','urn:uuid:493c469e-0a54-4aed-861a-9599a133841b','','',4,'/var/data/repo/work/535448cf-b6ff-4bb2-886f-ee81d05d517f','/var/data/repo/storage/pairtree_root/ur/n+/uu/id/+4/93/c4/69/e-/0a/54/-4/ae/d-/86/1a/-9/59/9a/13/38/41/b/data/00004/urn+uuid+493c469e-0a54-4aed-861a-9599a133841b','{\n    \"title\": \"Tallahassee Housing Prices as reported by Zillow\",\n    \"description\": \"Tallahassee Housing Prices as reported by Zillow, 20 records: Index, Square footage, beds, baths, zip code, year, list price. There is also an initial header line.\",\n    \"tags\": \"[]\",\n    \"userGeneratedTags\": \"[]\",\n    \"contactPoint\": \"Contact person\",\n    \"contactEmail\": \"contact@email.com\",\n    \"publisher\": \"Publishing organization\",\n    \"publisherEmail\": \"contact@email.com\",\n    \"language\": \"English\",\n    \"processId\": \"535448cf-b6ff-4bb2-886f-ee81d05d517f\",\n    \"date\": \"07.04.2020\",\n    \"lastChange\": \"2020-04-07T17:12:02Z\",\n    \"created\": \"2020-04-07T17:12:02Z\",\n    \"representations\": {\n        \"63eda280-493a-4d6c-a196-c8a9773babd9\": {\n            \"distribution_label\": \"csv\",\n            \"distribution_description\": \"CSV file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/63eda280-493a-4d6c-a196-c8a9773babd9/data/zillow.csv\"\n            ]\n        },\n        \"1f66edb8-d363-4307-85b2-e8f38cf245a2\": {\n            \"distribution_label\": \"ods\",\n            \"distribution_description\": \"Open Document Spreadsheet file\",\n            \"access_rights\": \"free\",\n            \"file_items\": [\n                \"representations/1f66edb8-d363-4307-85b2-e8f38cf245a2/data/zillow.ods\"\n            ]\n        }\n    },\n    \"nodeNamespaceId\": \"repo\",\n    \"repoIdentifier\": \"urn:uuid:2baa45fb-145e-44f4-895f-54ead5ab5eb7\",\n    \"repoTitle\": \"Conduit\",\n    \"repoDescription\": \"Data Repository\",\n    \"repoCatalogueIssued\": \"2020-01-01T12:00:00Z\",\n    \"repoCatalogueModified\": \"2020-02-01T12:00:00Z\"\n}','2020-04-07 17:12:10.000000','2020-03-27 22:23:01.756881',0,1);
/*!40000 ALTER TABLE `informationpackage` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

--
-- Table structure for table `internalidentifier`
--

DROP TABLE IF EXISTS `internalidentifier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `internalidentifier` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `org_nsid` varchar(200) NOT NULL,
  `identifier` varchar(200) NOT NULL,
  `created` datetime(6) NOT NULL,
  `used` tinyint(1) NOT NULL,
  `is_blockchain_id` tinyint(1) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `internalidentifier_user_id_4f238672` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `internalidentifier`
--

LOCK TABLES `internalidentifier` WRITE;
/*!40000 ALTER TABLE `internalidentifier` DISABLE KEYS */;
INSERT INTO `internalidentifier` VALUES (1,'eark','cnwsevzrrynodxoroxojopkdfsgblgyypfkkrgxi','2020-03-06 13:25:31.912673',1,0,NULL),(2,'eark','cembexygiiabbdasbtfyfbnxsmrzuioixrzdgaag','2020-03-11 14:54:20.494495',0,0,NULL);
/*!40000 ALTER TABLE `internalidentifier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `representations`
--

DROP TABLE IF EXISTS `representations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `representations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `identifier` varchar(200) NOT NULL,
  `label` varchar(200) NOT NULL,
  `description` varchar(4096) NOT NULL,
  `license` varchar(200) NOT NULL,
  `accessRights` varchar(200) NOT NULL,
  `created` datetime(6) NOT NULL,
  `ip_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `representations_ip_id_35c50a05` (`ip_id`)
) ENGINE=MyISAM AUTO_INCREMENT=23 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `representations`
--

LOCK TABLES `representations` WRITE;
/*!40000 ALTER TABLE `representations` DISABLE KEYS */;
INSERT INTO `representations` VALUES (4,'dbshnfdvbrwlqnyntcofqebeehighorlmkhvayjq','png','PNG image','undefined','free','2020-02-28 09:48:21.850680',2),(17,'b6eb897d-a886-4700-9654-ad1513c12c61','gml','Geographical data in the Geography Markup Language (GML) together with a CSV file containing additional attributes.','undefined','free','2020-03-17 09:22:20.277692',3),(16,'btvvarwrvhmjeasepzartypsjmexaiguqyeirxeb','siard','SIARD representation','undefined','free','2020-03-12 09:58:00.881592',2),(18,'ded90639-6617-4d89-a269-4391e5121428','shp','Shapefile','undefined','free','2020-03-17 09:34:23.671902',3),(19,'2982cf06-99a0-4155-8c61-8f513f59f724','','Microsoft Word Document','undefined','free','2020-03-17 09:50:07.584160',4),(20,'45dd8d76-2587-4196-b2b7-e44f195c67c9','pdf','PDF document','undefined','free','2020-03-17 09:50:12.743265',4),(21,'fec2b2e4-a422-40fa-a439-b41824231865','jpg','JPEG images','undefined','free','2020-03-17 10:20:59.290362',5),(22,'77bbf229-739a-45d5-b6af-28c65c962175','txt','Text representation','undefined','free','2020-03-17 10:21:02.976756',5);
/*!40000 ALTER TABLE `representations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rest_framework_api_key_apikey`
--

DROP TABLE IF EXISTS `rest_framework_api_key_apikey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rest_framework_api_key_apikey` (
  `id` varchar(100) NOT NULL,
  `created` datetime(6) NOT NULL,
  `name` varchar(50) NOT NULL,
  `revoked` tinyint(1) NOT NULL,
  `expiry_date` datetime(6) DEFAULT NULL,
  `hashed_key` varchar(100) NOT NULL,
  `prefix` varchar(8) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `prefix` (`prefix`),
  KEY `rest_framework_api_key_apikey_created_c61872d9` (`created`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rest_framework_api_key_apikey`
--

LOCK TABLES `rest_framework_api_key_apikey` WRITE;
/*!40000 ALTER TABLE `rest_framework_api_key_apikey` DISABLE KEYS */;
INSERT INTO `rest_framework_api_key_apikey` VALUES ('sBafmMkE.pbkdf2_sha256$180000$0zwtPJVzT7en$gaBPaRyQsfsNxp6luUp4IJt35k9r7saDbbwTigTSHE0=','2020-03-06 13:52:02.691114','backend',0,NULL,'pbkdf2_sha256$180000$0zwtPJVzT7en$gaBPaRyQsfsNxp6luUp4IJt35k9r7saDbbwTigTSHE0=','sBafmMkE');
/*!40000 ALTER TABLE `rest_framework_api_key_apikey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testmodel`
--

DROP TABLE IF EXISTS `testmodel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testmodel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `firstname` varchar(200) NOT NULL,
  `lastname` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `taggit_tag`
--

DROP TABLE IF EXISTS `taggit_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taggit_tag`
--

LOCK TABLES `taggit_tag` WRITE;
/*!40000 ALTER TABLE `taggit_tag` DISABLE KEYS */;
INSERT INTO `taggit_tag` VALUES (1,'Crime-as-a-Service','caas'),(2,'Drugs','drugs'),(3,'Weapons','weapons'),(4,'Darknet','darknet'),(5,'Used','used'),(7,'','');
/*!40000 ALTER TABLE `taggit_tag` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;


--
-- Table structure for table `taggit_taggeditem`
--

DROP TABLE IF EXISTS `taggit_taggeditem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_taggeditem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `object_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `tag_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taggit_taggeditem_content_type_id_object_id_tag_id_4bb97a8e_uniq` (`content_type_id`,`object_id`,`tag_id`),
  KEY `taggit_taggeditem_object_id_e2d7d1df` (`object_id`),
  KEY `taggit_taggeditem_content_type_id_9957a03c` (`content_type_id`),
  KEY `taggit_taggeditem_tag_id_f4f5b767` (`tag_id`),
  KEY `taggit_taggeditem_content_type_id_object_id_196cc965_idx` (`content_type_id`,`object_id`)
) ENGINE=MyISAM AUTO_INCREMENT=23 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testmodel`
--

LOCK TABLES `testmodel` WRITE;
/*!40000 ALTER TABLE `testmodel` DISABLE KEYS */;
/*!40000 ALTER TABLE `testmodel` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-03-17 12:06:38
