<?php

require_once 'db_connect.php';
session_start();

$response = array();

if($_SERVER["REQUEST_METHOD"] === "POST") {
    // Validate and sanitize user_id
    if(isset($_POST['car_id']) && is_numeric($_POST['car_id'])) {
        $car_id = intval($_POST['car_id']);

        try {
            // Prepare and execute the SQL query
            $stmt = $conn->prepare("SELECT * FROM cars WHERE car_id = :car_id");
            $stmt->bindParam(':car_id', $car_id, PDO::PARAM_INT);
            $stmt->execute();
            $users = $stmt->fetchAll(PDO::FETCH_ASSOC);

            if($cars) {
                $response['status'] = 'success';
                $response['data'] = $users;
                $response['message'] = 'session updated uwu';
            } else {
                $response['status'] = 'error';
                $response['message'] = 'No car found with the given ID.';
            }
        } catch (PDOException $e) {
            $response['status'] = 'error';
            $response['message'] = 'Database error: ' . $e->getMessage();
        }
    } else {
        $response['status'] = 'error';
        $response['message'] = 'Invalid user ID.';
    }
} else {
    $response['status'] = 'error';
    $response['message'] = 'Invalid request method.';
}

// Return response as JSON
header('Content-Type: application/json');
echo json_encode($response);
