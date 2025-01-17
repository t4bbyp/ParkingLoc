<?php
session_start();

require_once 'db_connect.php';

$response = array();

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $car_id = $_POST['car_id'];
    $fields = [];
    $values = [];

    if (isset($_POST['car_nr']) && !empty($_POST['car_nr'])) {
        $fields[] = "car_nr = :car_nr";
        $values[':car_nr'] = $_POST['car_nr'];
    }
    if (isset($_POST['car_brand']) && !empty($_POST['car_brand'])) {
        $fields[] = "car_brand = :car_brand";
        $values[':car_brand'] = $_POST['car_brand'];
    }
    if (isset($_POST['car_model']) && !empty($_POST['car_model'])) {
        $fields[] = "car_model = :car_model";
        $values[':car_model'] = $_POST['car_model'];
    }
    if (isset($_POST['car_year']) && !empty($_POST['car_year'])) {
        $fields[] = "car_year = :car_year";
        $values[':car_year'] = $_POST['car_year'];
    }

    if (!empty($fields)) {
        $sql = "UPDATE cars SET " . implode(", ", $fields) . " WHERE car_id = :car_id";
        $values[':car_id'] = $car_id;

        try {
            $stmt = $conn->prepare($sql);
            foreach ($values as $key => $value) {
                $stmt->bindValue($key, $value);
            }

            if ($stmt->execute()) {
                $response['error'] = false;
                $response['message'] = 'Date modificate.';
            } else {
                $response['error'] = true;
                $response['message'] = 'Eroare în timpul actualizării. Încearcă din nou.';
            }
        } catch (PDOException $e) {
            $response['error'] = true;
            $response['message'] = 'Database error: ' . $e->getMessage();
        }
    } else {
        $response['error'] = true;
        $response['message'] = 'No fields to update';
    }
} else {
    $response['error'] = true;
    $response['message'] = 'Invalid request method';
}

header('Content-Type: application/json');
echo json_encode($response);
