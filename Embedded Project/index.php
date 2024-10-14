<?php
session_start();

// Enable error reporting
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Check if the user is logged in
if (!isset($_SESSION['loggedin']) || $_SESSION['loggedin'] !== true) {
    header('Location: login.php');
    exit;
}

// Database connection
$connect = mysqli_connect('localhost', 'phpviewer', '1234', 'practicedb');

// Check connection
if (!$connect) {
    die('Connection failed: ' . mysqli_connect_error());
}

// Create SQL statements to get the last row of each table
$query1 = 'SELECT VehicleCount, Date, Time, Car, Bus, Motorbike FROM TrafficCam1 ORDER BY Time DESC LIMIT 1';
$query2 = 'SELECT VehicleCount, Date, Time, Car, Bus, Motorbike FROM TrafficCam2 ORDER BY Time DESC LIMIT 1';
$query3 = 'SELECT Colour FROM TrafficLight1'; // Get the latest colour for TrafficLight1
$query4 = 'SELECT Colour FROM TrafficLight2'; // Get the latest colour for TrafficLight2

// Send queries to the database
$result1 = mysqli_query($connect, $query1);
$result2 = mysqli_query($connect, $query2);
$result3 = mysqli_query($connect, $query3);
$result4 = mysqli_query($connect, $query4);

// Fetch the last row of each table
$record1 = mysqli_fetch_assoc($result1);
$record2 = mysqli_fetch_assoc($result2);
$record3 = mysqli_fetch_assoc($result3);
$record4 = mysqli_fetch_assoc($result4);
?>

<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    <title>Traffic Light Control & Monitor</title>
    <meta http-equiv="refresh" content="2"> <!-- Refresh the page every 2 seconds -->
    <style>
        .container {
            display: flex;
            justify-content: space-between;
            padding: 20px;
        }
        .section {
            width: 45%;
            border: 1px solid #ccc;
            padding: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        .data {
            font-size: 14px;
            padding: 5px;
            background-color: #f9f9f9;
            border-radius: 5px;
            margin: 10px 0;
        }
        .buttons {
            display: flex;
            justify-content: center;
            margin-top: 10px;
        }
        button {
            padding: 5px 10px;
            font-size: 14px;
            cursor: pointer;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            margin: 0 5px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .alert {
            padding: 10px;
            margin: 20px 0;
            background-color: #f44336; /* Red */
            color: white;
            border-radius: 5px;
            text-align: center;
            position: relative;
            animation: fadeOut 2s forwards; /* Fade out animation */
        }
        .alert-success {
            background-color: #4CAF50; /* Green */
        }
        @keyframes fadeOut {
            0% { opacity: 1; }
            100% { opacity: 0; }
        }
    </style>
</head>
<body>
    <h1 style="text-align: center;">Traffic Light Control & Monitor</h1>

    <?php
    // Check for the message in the URL and display it
    if (isset($_GET['message'])) {
        $messageClass = strpos($_GET['message'], 'successfully') !== false ? 'alert-success' : 'alert';
        echo '<div class="' . $messageClass . '" id="message">' . htmlspecialchars($_GET['message']) . '</div>';
    }
    ?>

    <div class="container">
        <!-- Display data from TrafficCam1 -->
        <div class="section">
            <h2>Traffic Camera 1</h2>
            <?php if ($record1) { ?>
                <div class="data">
		Colour:        | <?php echo $record3['Colour']; ?><br> <!-- Last Colour from TrafficLight1 -->

                    Total Vehicles:  | <?php echo $record1['VehicleCount']; ?><br>
                    Cars:           | <?php echo $record1['Car']; ?><br>
                    Buses:          | <?php echo $record1['Bus']; ?><br>
                    Motorbikes:     | <?php echo $record1['Motorbike']; ?><br>
                    Date:          | <?php echo $record1['Date']; ?><br>
                    Time:          | <?php echo $record1['Time']; ?><br>
                </div>
            <?php } else {
                echo '<p>No data available from TrafficCam1.</p>';
            } ?>
            <div class="buttons">
                <form method="post" action="set_mode.php">
                    <input type="hidden" name="camera" value="TrafficCam1">
                    <input type="hidden" name="mode" value="manual">
                    <button type="submit">Manual</button>
                </form>
            </div>
        </div>

        <!-- Display data from TrafficCam2 -->
        <div class="section">
            <h2>Traffic Camera 2</h2>
            <?php if ($record2) { ?>
                <div class="data">
		Colour:        | <?php echo $record4['Colour']; ?><br> <!-- Last Colour from TrafficLight1 -->

                    Total Vehicles:  | <?php echo $record2['VehicleCount']; ?><br>
                    Cars:           | <?php echo $record2['Car']; ?><br>
                    Buses:          | <?php echo $record2['Bus']; ?><br>
                    Motorbikes:     | <?php echo $record2['Motorbike']; ?><br>
                    Date:          | <?php echo $record2['Date']; ?><br>
                    Time:          | <?php echo $record2['Time']; ?><br>
                </div>
            <?php } else {
                echo '<p>No data available from TrafficCam2.</p>';
            } ?>
            <div class="buttons">
                <form method="post" action="set_mode_manualTF2.php">
                    <input type="hidden" name="camera" value="TrafficCam2">
                    <input type="hidden" name="mode" value="manual">
                    <button type="submit">Manual</button>
                </form>
            </div>
        </div>
    </div>

    <div class="buttons" style="justify-content: center; margin-top: 20px;">
        <form method="post" action="set_mode_automatic.php">
            <button type="submit">Automatic</button>
        </form>
    </div>

    <a href="logout.php">Logout</a>

    <script>
        // Function to hide the message after 2 seconds
        window.onload = function() {
            const message = document.getElementById('message');
            if (message) {
                setTimeout(() => {
                    message.style.display = 'none';
                }, 3000); // Time in milliseconds
            }
        };
    </script>
</body>
</html>
