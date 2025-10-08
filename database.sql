-- SQL Script to Create Database and Import Data
-- Database: online_portal

CREATE DATABASE IF NOT EXISTS `online_portal`;
USE `online_portal`;

-- --------------------------------------------------------
-- Table structure for table `users`
-- --------------------------------------------------------

CREATE TABLE `users` (
  `id` varchar(10) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `role` enum('student','teacher','admin') NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `users` VALUES
('A001', 'admin1', '1234', 'admin', 'Admin One', 'admin@example.com'),
('S101', 'student1', '1234', 'student', 'Student One', 's1@example.com'),
('S102', 'student2', '1234', 'student', 'Student Two', 's2@example.com'),
('S103', 'student3', '1234', 'student', 'Student Three', 's3@example.com'),
('S104', 'student4', '1234', 'student', 'Student Four', 's4@example.com'),
('S105', 'student5', '1234', 'student', 'Student Five', 's5@example.com'),
('T201', 'teacher1', '1234', 'teacher', 'Teacher One', 't1@example.com'),
('T202', 'teacher2', '1234', 'teacher', 'Teacher Two', 't2@example.com'),
('T203', 'teacher3', '1234', 'teacher', 'Teacher Three', 't3@example.com');

-- --------------------------------------------------------
-- Table structure for table `subjects`
-- --------------------------------------------------------

CREATE TABLE `subjects` (
  `id` varchar(10) NOT NULL,
  `name` varchar(50) NOT NULL,
  `teacher_id` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `teacher_id` (`teacher_id`),
  CONSTRAINT `subjects_ibfk_1` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `subjects` VALUES
('SUB1', 'Python', 'T201'),
('SUB2', 'Java', 'T202'),
('SUB3', 'C', 'T203');

-- --------------------------------------------------------
-- Table structure for table `assignments`
-- --------------------------------------------------------

CREATE TABLE `assignments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `subject_id` varchar(10) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_subject` (`subject_id`),
  CONSTRAINT `fk_subject` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `assignments` VALUES
(2, 'SUB1', 'as2', 'do it', '2025-10-10', NULL, '2025-10-05 10:53:24');

-- --------------------------------------------------------
-- Table structure for table `submissions`
-- --------------------------------------------------------

CREATE TABLE `submissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `assignment_id` int(11) NOT NULL,
  `student_id` varchar(10) NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `submitted_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` varchar(20) DEFAULT 'Pending',
  `marks` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_assignment` (`assignment_id`),
  KEY `fk_student` (`student_id`),
  CONSTRAINT `fk_assignment` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_student` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `submissions` VALUES
(3, 2, 'S101', 'uploads/java_certficate.pdf', '2025-10-05 11:21:35', 'Submitted', 10);

-- --------------------------------------------------------
-- Table structure for table `attendance`
-- --------------------------------------------------------

CREATE TABLE `attendance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` varchar(10) DEFAULT NULL,
  `subject_id` varchar(10) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `status` enum('Present','Absent') DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  KEY `subject_id` (`subject_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`),
  CONSTRAINT `attendance_ibfk_2` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `attendance` VALUES
(1, 'S101', 'SUB1', '2025-10-05', 'Present'),
(2, 'S102', 'SUB1', '2025-10-05', 'Absent'),
(3, 'S103', 'SUB1', '2025-10-05', 'Absent'),
(4, 'S104', 'SUB1', '2025-10-05', 'Absent'),
(5, 'S105', 'SUB1', '2025-10-05', 'Absent'),
(6, 'S101', 'SUB1', '2025-10-06', 'Absent'),
(7, 'S102', 'SUB1', '2025-10-06', 'Present'),
(8, 'S103', 'SUB1', '2025-10-06', 'Present'),
(9, 'S104', 'SUB1', '2025-10-06', 'Present'),
(10, 'S105', 'SUB1', '2025-10-06', 'Present'),
(11, 'S101', 'SUB1', '2025-10-07', 'Present'),
(12, 'S102', 'SUB1', '2025-10-07', 'Present'),
(13, 'S103', 'SUB1', '2025-10-07', 'Present'),
(14, 'S104', 'SUB1', '2025-10-07', 'Absent'),
(15, 'S105', 'SUB1', '2025-10-07', 'Present'),
(16, 'S101', 'SUB1', '2025-10-08', 'Present'),
(17, 'S102', 'SUB1', '2025-10-08', 'Present'),
(18, 'S103', 'SUB1', '2025-10-08', 'Absent'),
(19, 'S104', 'SUB1', '2025-10-08', 'Present'),
(20, 'S105', 'SUB1', '2025-10-08', 'Present'),
(21, 'S101', 'SUB2', '2025-10-08', 'Present'),
(22, 'S102', 'SUB2', '2025-10-08', 'Present'),
(23, 'S103', 'SUB2', '2025-10-08', 'Present'),
(24, 'S104', 'SUB2', '2025-10-08', 'Present'),
(25, 'S105', 'SUB2', '2025-10-08', 'Present');

-- --------------------------------------------------------
-- Table structure for table `queries`
-- --------------------------------------------------------

CREATE TABLE `queries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` varchar(10) NOT NULL,
  `teacher_id` varchar(10) NOT NULL,
  `subject_id` varchar(10) NOT NULL,
  `query_text` text NOT NULL,
  `reply` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  KEY `teacher_id` (`teacher_id`),
  KEY `subject_id` (`subject_id`),
  CONSTRAINT `queries_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `queries_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `queries_ibfk_3` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `queries` VALUES
(1, 'S101', 'T201', 'SUB1', 'when is the next quiz?', 'this weekened', '2025-10-05 18:38:55');

COMMIT;
