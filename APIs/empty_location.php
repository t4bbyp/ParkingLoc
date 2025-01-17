<?php
require_once 'db_connect.php';

$response = array();

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $car_id = $_POST['car_id'];
    
    $stmt = $conn->prepare("UPDATE cars SET car_location = '' WHERE car_id = :car_id");
    $stmt->bindParam(':car_id', $car_id, PDO::PARAM_INT);

    if ($stmt->execute()) {
        $response['error'] = false;
        $response['message'] = 'Location emptied.';
    } else {
        $response['error'] = true;
        $response['message'] = 'Error while emptying location.';
    }
} else {
    $response['error'] = true;
    $response['message'] = 'Invalid request.';
}

echo json_encode($response);
