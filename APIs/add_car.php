<?php

require_once 'db_connect.php';
session_start();

$response = array();

if ($_SERVER["REQUEST_METHOD"] === "POST") {
        $user_id = $_POST['user_id'];
        $car_nr = $_POST['car_nr'];
        $car_brand = $_POST['car_brand'];
        $car_model = $_POST['car_model'];
        $car_year = $_POST['car_year'];

        $stmt = $conn->prepare("INSERT INTO cars (car_nr, user_id, car_brand, car_model, car_year) VALUES (:car_nr, :user_id, :car_brand, :car_model, :car_year)");
        $stmt->bindParam(':car_nr', $car_nr, PDO::PARAM_STR);
        $stmt->bindParam(':user_id', $user_id, PDO::PARAM_INT);
        $stmt->bindParam(':car_brand', $car_brand, PDO::PARAM_STR);
        $stmt->bindParam(':car_model', $car_model, PDO::PARAM_STR);
        $stmt->bindParam(':car_year', $car_year, PDO::PARAM_INT);
        
        
        if($stmt->execute()) {
            $response['error'] = false;
            $response['message'] = 'Autovehicul înregistrat cu succes.';
        } else {
            $response['error'] = true;
            $response['message'] = 'Autovehiculul nu a putut fi înregistrat. Încercați din nou.';
        }
} else {
                $response['error'] = true;
                $response['message'] = 'Autovehiculul nu a putut fi înregistrat. Contactați administratorul pentru ajutor suplimentar.';
            }
echo json_encode($response);
