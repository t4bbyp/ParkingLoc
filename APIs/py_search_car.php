<?php
header('Content-Type: application/json');
require_once 'db_connect.php';

$response = [];

if($_SERVER["REQUEST_METHOD"] === "GET") {
    if (!isset($_GET['car_nr'])) {
        echo json_encode(['error' => 'Missing car_nr parameter']);
        exit();
    }

    $car_nr = $_GET['car_nr'];
    
    if (empty($car_nr)) {
        echo json_encode(['error' => 'car_nr cannot be empty']);
        exit();
    }
    
    try {
        $stmt = $conn->prepare("SELECT car_id, car_nr FROM cars WHERE car_nr = :car_nr");
        $stmt->bindParam(':car_nr', $car_nr, PDO::PARAM_STR);
        $stmt->execute();
        
        $car = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if($car) {
            $response['error'] = false;
            $response['message'] = "Car data exists.";
            $response['car_details'] = array(
                'car_id' => $car['car_id'],
                'car_nr' => $car['car_nr']
            );
        } else {
            $response['error'] = true;
            $response['message'] = 'Car not found';
        }
    } catch (PDOException $e) {
        $response['error'] = true;
        $response['message'] = 'Database query error: ' . $e->getMessage();
    }
} else {
    $response['error'] = true;
    $response['message'] = 'Invalid request method';
}

echo json_encode($response);
