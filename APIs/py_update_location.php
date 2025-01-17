<?php
header('Content-Type: application/json');
require_once 'db_connect.php';

$response = [];

if($_SERVER["REQUEST_METHOD"] === "POST"){
    $car_id = $_POST['car_id'];
    $car_location = $_POST['car_location'];
    
    try{
        $stmt = $conn->prepare("UPDATE cars SET car_location = :car_location WHERE car_id = :car_id");
        $stmt->bindParam(':car_id', $car_id, PDO::PARAM_INT);
        $stmt->bindParam(':car_location', $car_location);
        
        if($stmt->execute()) {
            $response['error'] = false;
            $response['message'] = 'Location changed.';
        } else {
            $response['error'] = true;
            $response['message'] = 'Error changing location';
        }   
    } catch (PDOException $e) {
        $response['error'] = true;
        $response['message'] = 'Database query error: ' . $e->getMessage();
    }
} else {
    $response['error'] = true;
    $response['message'] = 'idfk man';
}

echo json_encode($response);
