<?php
session_start();

// Turn on error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

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

// Function to set mode to "manual"
function setModeToManual($tableName, $connect) {
    // Delete any existing entries in the Mode column
    $deleteQuery = "DELETE FROM $tableName";
    mysqli_query($connect, $deleteQuery);

    // Insert the new mode
    $insertQuery = "INSERT INTO $tableName (Mode) VALUES ('Manual')";

    if (mysqli_query($connect, $insertQuery)) {
        return "Record inserted successfully into $tableName.";
    } else {
        return "Error inserting record into $tableName: " . mysqli_error($connect);
    }
}

// Set "manual" into TrafficCam1Mode
$responseMessage = setModeToManual('TrafficCam1Mode', $connect);

// Close the database connection
mysqli_close($connect);

$responseMessage = "Traffic Light 1 Manual Mode";

// Redirect back to index page with a success message
header('Location: index.php?message=' . urlencode($responseMessage));
exit;
?>
