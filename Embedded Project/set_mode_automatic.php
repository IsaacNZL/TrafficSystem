<?php
session_start();

// Check if the user is logged in
if (!isset($_SESSION['loggedin']) || $_SESSION['loggedin'] !== true) {
    header('Location: login.php');
    exit;
}

// Database connection
$connect = mysqli_connect('localhost', 'phpviewer', '1234', 'practicedb');

if (!$connect) {
    die("Connection failed: " . mysqli_connect_error());
}

// Function to set mode
function setMode($tableName, $mode, $connect) {
    // Delete any existing entries in the Mode column
    $deleteQuery = "DELETE FROM $tableName";
    mysqli_query($connect, $deleteQuery);

    // Insert the new mode
    $insertQuery = "INSERT INTO $tableName (Mode) VALUES ('$mode')";

    if (mysqli_query($connect, $insertQuery)) {
        echo "Record inserted successfully into $tableName.<br>";
    } else {
        echo "Error inserting record into $tableName: " . mysqli_error($connect) . "<br>";
    }
}

// Set "automatic" into TrafficCam1Mode
setMode('TrafficCam1Mode', 'Automatic', $connect);

// Set "automatic" into TrafficCam2Mode
setMode('TrafficCam2Mode', 'Automatic', $connect);

mysqli_close($connect);

$responseMessage = "Lights in Auto Mode"; // New message

// Redirect back to index page with a success message
header('Location: index.php?message=' . urlencode($responseMessage));
exit;

?>
