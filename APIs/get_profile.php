<?php

require_once 'db_connect.php';
session_start();

$response = array();

if($_SERVER["REQUEST_METHOD"] === "POST") {
    if(isset($_POST['user_id']) && is_numeric($_POST['user_id'])) {
        $user_id = intval($_POST['user_id']);
        
        try {
            $stmt = $conn->prepare("SELECT user_id, user_lastname, user_firstname, user_email FROM users WHERE user_id = :user_id");
            $stmt->bindParam(':user_id', $user_id, PDO::PARAM_INT);
            $stmt->execute();
            $users = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            if($users) {
                $response['status'] = 'success';
                $response['data'] = $users;
                $response['message'] = 'Session updated.';
            } else {
                $response['status'] = 'error';
                $response['message'] = 'No user found with the given ID.';
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
