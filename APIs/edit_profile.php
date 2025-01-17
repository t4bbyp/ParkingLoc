<?php
session_start();

require_once 'db_connect.php'; // Include the database connection file

$response = array();

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $user_id = $_POST['user_id'];
    $fields = [];
    $values = [];

    if (isset($_POST['user_lastname']) && !empty($_POST['user_lastname'])) {
        $fields[] = "user_lastname = :user_lastname";
        $values[':user_lastname'] = $_POST['user_lastname'];
    }
    if (isset($_POST['user_firstname']) && !empty($_POST['user_firstname'])) {
        $fields[] = "user_firstname = :user_firstname";
        $values[':user_firstname'] = $_POST['user_firstname'];
    }
    if (isset($_POST['user_email']) && !empty($_POST['user_email'])) {
        $fields[] = "user_email = :user_email";
        $values[':user_email'] = $_POST['user_email'];
    }

    if (!empty($fields)) {
        $sql = "UPDATE users SET " . implode(", ", $fields) . " WHERE user_id = :user_id";
        $values[':user_id'] = $user_id;

        try {
            $stmt = $conn->prepare($sql);
            foreach ($values as $key => $value) {
                $stmt->bindValue($key, $value);
            }

            if ($stmt->execute()) {
                $response['error'] = false;
                $response['message'] = 'User edited.';
            } else {
                $response['error'] = true;
                $response['message'] = 'Error while editing user';
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
