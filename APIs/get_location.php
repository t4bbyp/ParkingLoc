<?php

require_once 'db_connect.php';
session_start();

$response = array();

if($_SERVER["REQUEST_METHOD"] === "POST") {
    $user_id = $_POST['user_id'];
    
    // Prepare and execute the SQL query
$stmt = $conn->prepare("SELECT * FROM cars WHERE user_id = :user_id");
$stmt->bindParam(':user_id', $user_id, PDO::PARAM_INT);
$stmt->execute();
$location = $stmt->fetchAll(PDO::FETCH_ASSOC);
}

// Return contacts as JSON
echo json_encode($location);
