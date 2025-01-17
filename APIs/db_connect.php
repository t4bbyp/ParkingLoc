<?php

$servername = "localhost";
$username = "parkingtori";
$password = "w*h9q4^)N)#T";
$dbname = "parkingtori_db";

try {
    $conn = new PDO("mysql:host=$servername;dbname=$dbname", $username, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $conn->exec("SET NAMES utf8mb4");
} catch(PDOException $e) {
    die("Connection failed: " . $e->getMessage());
}
