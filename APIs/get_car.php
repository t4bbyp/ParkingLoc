<?php

require_once 'db_connect.php';
session_start();

$response = array();

if($_SERVER["REQUEST_METHOD"] === "POST") {
    if(isset($_POST['car_id']) && is_numeric($_POST['car_id'])) {
        $car_id = intval($_POST['car_id']);

        try {
            $stmt = $conn->prepare("SELECT * FROM cars WHERE car_id = :car_id");
            $stmt->bindParam(':car_id', $car_id, PDO::PARAM_INT);
            $stmt->execute();
            $users = $stmt->fetchAll(PDO::FETCH_ASSOC);

            if($cars) {
                $response['status'] = 'success';
                $response['data'] = $users;
                $response['message'] = 'Sesiune actualizată cu succes.';
            } else {
                $response['status'] = 'error';
                $response['message'] = 'Nu s-a găsit autovehiculul.';
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

header('Content-Type: application/json');
echo json_encode($response);
