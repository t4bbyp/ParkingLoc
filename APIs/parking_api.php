<?php

require_once 'db_connect.php';
$response = array();

if (isset($_GET['apicall'])) {
    switch ($_GET['apicall']) {
        case 'register':
            // Verifică datele
            if (ParamValidation(array('user_email', 'user_password'))) {

                $user_email = $_POST['user_email'];
                $user_password = $_POST['user_password'];
                $user_lastname = $_POST['user_lastname'];
                $user_firstname = $_POST['user_firstname'];

                // Verifică dacă utilizatorul există deja în funcție de adresa de email
                $stmt = $conn->prepare("SELECT user_id FROM users WHERE user_email = :user_email");
                $stmt->bindParam(':user_email', $user_email);
                $stmt->execute();
                $user = $stmt->fetch(PDO::FETCH_ASSOC);

                
                // Dacă există
                if ($user) {
                    $response['error'] = true;
                    $response['message'] = 'Există deja un cont cu această adresă de email.';
                } else {
                    $hashedPassword = password_hash($user_password, PASSWORD_BCRYPT);
                    
                    // Adaugă datele introduse în tabelă
                    $stmt = $conn->prepare("INSERT INTO users (user_email, user_password, user_lastname, user_firstname) VALUES (:user_email, :user_password, :user_lastname, :user_firstname)");
                
                    $stmt->bindParam(':user_email', $user_email);
                    $stmt->bindParam(':user_password', $hashedPassword);
                    $stmt->bindParam(':user_lastname', $user_lastname);
                    $stmt->bindParam(':user_firstname', $user_firstname);

                    // Dacă utilizatorul este adăugat în baza de date
                    if ($stmt->execute()) {
                        // Preia datele
                        $stmt = $conn->prepare("SELECT user_id, user_email FROM users WHERE user_email = :user_email");
                        $stmt->bindParam(":user_email", $user_email);
                        $stmt->execute();
                        $user = $stmt->fetch(PDO::FETCH_ASSOC);

                        // Adaugă datele în răspuns
                        $response['error'] = false;
                        $response['message'] = "Cont creat cu succes.";
                        $response['user'] = $user;
                    } else {
                        $response['error'] = true;
                        $response['message'] = "Eroare în timpul înregistrării. Încercați din nou.";
                    }
                }
            } else {
                $response['error'] = true;
                $response['message'] = 'Datele introduse nu sunt valide.';
            }

            break;

            case 'login':
                if (ParamValidation(array('user_email', 'user_password'))) {
                    // Primește credențialele din request
                    $user_email = $_POST['user_email'];
                    $user_password = $_POST['user_password'];
            
                    $stmt = $conn->prepare("SELECT user_id, user_email, user_password, user_firstname, user_lastname FROM users WHERE user_email = :user_email");
                    $stmt->bindParam(':user_email', $user_email);
                    $stmt->execute();
                    $user = $stmt->fetch(PDO::FETCH_ASSOC);
            
                    // Dacă există cont
                    if ($user) {
                        // Verifică parola
                        if (password_verify($user_password, $user['user_password'])) {
                            session_start();
                            $_SESSION['user_id'] = $user['user_id'];
                            $response['error'] = false;
                            $response['message'] = 'Autentificare cu succes.';
                            $response['detalii_user'] = array();
            
                            $user_details = array(
                                'user_id' => $user['user_id'],
                                'user_email' => $user['user_email'],
                                'user_firstname' => $user['user_firstname'],
                                'user_lastname' => $user['user_lastname']
                            );
                            array_push($response['detalii_user'], $user_details);
                        } else {
                            // Dacă parola este greșită
                            $response['error'] = true;
                            $response['message'] = "Email sau parolă greșite.";
                        }
                    } else {
                        $response['error'] = true;
                        $response['message'] = 'Email sau parolă greșite.';
                    }
                } else {
                    $response['error'] = true;
                    $response['message'] = 'Datele nu sunt valide.';
                }
                break;


        default:
            $response['error'] = true;
            $response['message'] = 'Operație eșuată.';
    }
} else {
    $response['error'] = true;
    $response['message'] = 'Invalid API call';
}

header('Content-Type: application/json');

echo json_encode($response);

function ParamValidation($params)
{
    foreach ($params as $param) {
        if (!isset($_POST[$param])) {
            return false;
        }
    }
    return true;
}
