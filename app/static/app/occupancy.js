'use strict';

var occupancyApp = angular.module('occupancyApp', [
  'ngRoute',
  'pikaday',
  'chart.js'
]);

occupancyApp.controller('dashboardController', ['$scope', '$http', 'chartData', function($scope, $http, chartData) {
    $scope.message = "Hello Admin";

    $scope.submit = function() {
      // Mon Jul 04 2016
      // var dateRe = new RegExp("[A-Za-z]{3} [A-Za-z]{3} \d{2} \d{4}");
      // var testRe = new RegExp("a");
      // var testString = "able";
      // console.log(testRe.test(testString));
      // console.log(dateRe.test($scope.formData.date));
      // if (dateRe.test($scope.date)) {
      //   console.log("matches");
      // }
      

      if ($scope.formData.room && $scope.formData.date) {
        // formatting the URL
        var url = "http://localhost:5000/api/room/occupancy/"+ $scope.formData.room +"/" + $scope.formData.date.split(" ").join("%20");
        console.log("making request to " + url);
        $http.get(url).then(function successCallback(response) {
          
          var hours = [];

          // separates results into unique hours
          response.data.results.map(function(item, index) {
            var subStr = item.counts_time.substring(11, 13) * 1
            // if the hour has already been listed then push it onto the hours array at a specific index
            if (hours[subStr]) {
              hours[subStr].push(item);
            } else {
              hours[subStr] = [item];
            }

          });

          console.log(hours);

          // cycle through each hour
          var reducedData = hours.map(function(item) {

            // reduce the items to a single total value
            var reduced = item.reduce(function(total, i){
              
              return (total + (i.counts_authenticated / 1))
            }, 0);

            // return the average
            return reduced / item.length
          });
          
          // set the chart data
          $scope.data = [reducedData];
          $scope.series = ['% occupied'];

          // build the labels
          $scope.labels = reducedData.map(function(item, index) {
            return "Hour " + index;
          });
          
          
          $scope.options = {
            responsive: true
          }
          $scope.onClick = function (points, evt) {
            console.log(points, evt);
          };

          
        }, function errorCallback(response) {
          // called asynchronously if an error occurs
          // or server returns response with an error status.
        });
      }
    }
}]);

occupancyApp.controller("lineCtrl", ['$scope', '$timeout', 'chartData', function ($scope, $timeout, chartData) {

  //$scope.labels = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"];
  $scope.series = ['% occupied'];

  // build the labels
  $scope.labels = chartData.data.map(function(item, index) {
    return "Hour " + index;
  });

  console.log("charting");
  // get the data
  $scope.data = [
    chartData.data
  ];
  $scope.options = {
    responsive: true
  }
  $scope.onClick = function (points, evt) {
    console.log(points, evt);
  };
}]);


occupancyApp.controller("uploadController", ["$scope", function($scope) {
  console.log("uploadController");
}]);

occupancyApp.controller('loginController', ['$scope', '$location', function($scope, $location){
  $scope.message = "";
  $scope.submit = function() {
      if ($scope.username == "admin") {
        // successful login
        console.log("success");
        $location.path("/dashboard");
      }
  }
}]);
