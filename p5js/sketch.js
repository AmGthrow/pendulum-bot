// DISCLAIMER: This is DEFINITELY NOT a physics simulation. It looks pretty decent but I've had to hardcode a lot 
// of "failsafes" since I encountered a lot of wonky physics like pendulums speeding up infinitely (it still does that sometimes).
// It looks realistic-ish but just don't cite this in your university paper is what I'm saying.

let capturer;
let btn;
function record() {
  capturer = new CCapture({
    format: "png",  // the final .mp4 is actually composed of individual .png frames
    verbose: "false",
    quality: 40,
  });
  capturer.start();
  btn.textContent = "stop recording";
  btn.onclick = e => {
    capturer.stop();
    capturer.save();
    capturer = null;
    btn.textContent = "start recording";
    btn.onclick = record;
  };
}
//################################################################################ Everything above this line is for CCapture.js

function randomBetween(min, max){  // returns a random number between <min> and <max>
  return (Math.random() * (max - min) + min);
}
var PI = Math.PI;

var WINDOW_SIZE = [1280, 720];
var g = 9.8 / (60 * 60); // gravity should be m/s^2 but in p5, 1 second is 1 frame (at least that's what someone in YT comments said). Since we play at 60fps, s^2 should be 60^2

var DICT_PARAMETERS = {}; // Dictionary of all my starting parameters (feel free to play around w the values)
DICT_PARAMETERS['a1_v'] = 0;
DICT_PARAMETERS['a2_v'] = 0;
DICT_PARAMETERS['a1'] = randomBetween(3*PI/2, PI/2); // formula is Math.random * (max-min) + min, I'll get a floating point number between max and min    
DICT_PARAMETERS['a2'] = randomBetween(2*PI, 0);
DICT_PARAMETERS['m1'] = randomBetween(2, 1);
DICT_PARAMETERS['m2'] = randomBetween(2 * DICT_PARAMETERS.m1, 0.5 * DICT_PARAMETERS.m1);
DICT_PARAMETERS['r1'] = randomBetween(1 * DICT_PARAMETERS.m1, 0.5 * DICT_PARAMETERS.m1);
DICT_PARAMETERS['r2'] = randomBetween(1 * DICT_PARAMETERS.r1, 0.5 * DICT_PARAMETERS.r1);
// I can't make DICT_PARAMETERS in one go the way I do with DICT_DIFFERENCE because my rods' lengths scale off of my weights' masses
// If I didn't do that, I might have very heavy weights with short rods or light weights with very long rods and they make very ugly pendulums

var DICT_DIFFERENCE = { // Dictionary of all my offsets (you can change the values here too)
  'a1_v': 0,         // dictionary of values that dictate how different each pendulum's parameters are relative to each other            
  'a2_v': 0,           // a value of 0.0 means all pendulums have the same value for that parameter  
  'a1': 0,             // a value of 0.1 means all pendulums are off by 0.1 units from each other
  'a2': 0,
  'm1': 0,
  'm2': 0,
  'r1': 0,
  'r2': 0,
};

// Randomly pick a parameter from DICT_DIFFERENCE and randomize that
var keyList = [];
for(key in DICT_DIFFERENCE) keyList.push(key);
var offsetParam = keyList[Math.floor(randomBetween(keyList.length,2))]; // contains one of the parameters (e.g. a1, m2, r1, etc.) EXCEPT a1_v and a2_v since I don't want to randomize those
DICT_DIFFERENCE[offsetParam] = randomBetween(0.01, 0.001);
if(offsetParam.includes('a')) DICT_DIFFERENCE[offsetParam] *= 100; //  A difference of 1 degree is worth a lot less than an offset of 1kg or 1m, so I compensate by scaling the offset for angles up

// NOTE: There's no point adding a1_a and a2_a since they'll get overwritten the instant I calculate the 'real' acceleration

// These are just global variables that I need across multiple functions. I need them globally because I use them in both setup() and draw()
var SCALE_LEN;
var SCALE_MASS;
var pendulums = [], traces = [], rand;
var numPendulums = 7; // The number of pendulums I'm drawing. I usually do 7 because of 7 colors in ROYGBIV
var longestRod = 0;

function Line(x, y) {   // Represents the "traced out path" that each of the pendulums leave a trail of

  this.x = x; // this.x and this.y represent the pendulum's current position
  this.y = y;
  this.history = [createVector(this.x, this.y)];  //array of up to 100 points which traces out the pendulum's path

  this.update = function (x, y) {
    this.x = x;
    this.y = y;
    this.history.push(createVector(this.x, this.y));
    if (this.history.length > 100) this.history.shift();
  }

  this.show = function (lineColor = color(255, 255, 255)) {
    for (let i = 0; i < this.history.length - 1; i++) {
      lineColor.setAlpha(map(i, 0, this.history.length, 0, 255)); // This line gives the path a "fading" effect
      stroke(lineColor);
      strokeWeight(3);
      line(this.history[i].x, this.history[i].y, this.history[i + 1].x, this.history[i + 1].y);
      stroke(0);
      strokeWeight(1);

    }
  }
  this.clear = function () {
    this.history = [];
  }

}

function Pendulum(pendulumNo = 0) {  // Represents each pendulum. The pendulumNo is for offsetting each pendulum by DICT_DIFFERENCE[key]
  // The first pendulum is offset by 0 * DICT_DIFFERENCE[key], 2nd one by 1 * DICT_DIFFERENCE[key], 3rd by 2 * DICT_DIFFERENCE[key], etc.
  this.a1 = DICT_PARAMETERS.a1 + pendulumNo * radians(DICT_DIFFERENCE.a1); // initial angle
  this.a2 = DICT_PARAMETERS.a2 + pendulumNo * radians(DICT_DIFFERENCE.a2);

  this.a1_v = DICT_PARAMETERS.a1_v + pendulumNo * DICT_DIFFERENCE.a1_v;  //angular velocity
  this.a2_v = DICT_PARAMETERS.a2_v + pendulumNo * DICT_DIFFERENCE.a2_v;

  this.r1 = DICT_PARAMETERS.r1 + pendulumNo * DICT_DIFFERENCE.r1;
  this.r2 = DICT_PARAMETERS.r2 + pendulumNo * DICT_DIFFERENCE.r2;
  // know that this value is arbitrarily determined and I just wrote this equation based on what I think "looks good": the rods should take up 60% of the screen's height when fully extended
  this.m1 = DICT_PARAMETERS.m1 + pendulumNo * DICT_DIFFERENCE.m1; // mass of each pendulum
  this.m2 = DICT_PARAMETERS.m2 + pendulumNo * DICT_DIFFERENCE.m2;

  // The equations in this.update have a coordinate system where 0 degrees is straight down and 90 degrees is left. I had to 
  // swap sin and cos, as well as use negative sin, to transform the coordinate system of p5js to the one in the equations
  this.x1 = this.r1 * -sin(this.a1); //position of 1st mass is length of rod 1 times angle of rod 1
  this.y1 = this.r1 * cos(this.a1);

  this.x2 = this.x1 + this.r2 * -sin(this.a2); //position of 2nd mass is position of 1st mass plus (length of rod 2 times angle of rod 2)
  this.y2 = this.y1 + this.r2 * cos(this.a2);

  this.compare = function (comparePendulum) {  // Returns the initial parameters and offsets
    message = `Parameters: a1=${(270 - degrees(this.a1)).toFixed(2)}° a2=${(270 - degrees(this.a2)).toFixed(2)}° r1=${this.r1.toFixed(2)}m r2=${this.r2.toFixed(2)}m m1=${this.m1.toFixed(2)}kg m2=${this.m2.toFixed(2)}kg\n\nOffset/s:`;
    for (var [key, value] of Object.entries(DICT_DIFFERENCE)) {
      if (value != 0.0) {
        value = value.toFixed(4);
        message = message.concat(`\n${key} offset by ${value}`);
        if (key.includes('a')) message = message.concat('°');
        if (key.includes('m')) message = message.concat('kg');
        if (key.includes('r')) message = message.concat('m');
      }
    }
    return (message);
  }


  this.update = function () {  // Calculates angular acceleration of each mass of the pendulum


    // Derivation of the equations below can be found at https://www.myphysicslab.com/pendulum/double-pendulum-en.html

    // This whole chunk is to get angular acceleration of the first pendulum
    let num1 = -g * (2 * this.m1 + this.m2) * sin(this.a1);
    let num2 = -this.m2 * g * sin(this.a1 - 2 * this.a2);
    let num3 = -2 * sin(this.a1 - this.a2) * this.m2;
    let num4 = this.a2_v * this.a2_v * this.r2 + this.a1_v * this.a1_v * this.r1 * cos(this.a1 - this.a2);
    let den = this.r1 * (2 * this.m1 + this.m2 - this.m2 * cos(2 * this.a1 - 2 * this.a2));
    this.a1_a = (num1 + num2 + num3 * num4) / den;

    // This whole chunk is to get angular acceleration of the second pendulum
    num1 = 2 * sin(this.a1 - this.a2);
    num2 = this.a1_v * this.a1_v * this.r1 * (this.m1 + this.m2);
    num3 = g * (this.m1 + this.m2) * cos(this.a1);
    num4 = this.a2_v * this.a2_v * this.r2 * this.m2 * cos(this.a1 - this.a2);
    den = this.r2 * (2 * this.m1 + this.m2 - this.m2 * cos(2 * this.a1 - 2 * this.a2));
    this.a2_a = (num1 * (num2 + num3 + num4)) / den;

    this.a1_v += this.a1_a;
    this.a2_v += this.a2_a;

    this.a1 += this.a1_v;
    this.a2 += this.a2_v;

    this.x1 = this.r1 * -sin(this.a1);
    this.y1 = this.r1 * cos(this.a1);

    this.x2 = this.x1 + this.r2 * -sin(this.a2);
    this.y2 = this.y1 + this.r2 * cos(this.a2);

    /*
    DEV NOTE: Sometimes the pendulums start speeding up and get out of control. Unless the calculations above are
    wrong, I don't actually know what's causing the spontaneous acceleration. For now, I'm bodging together a 
    crummy solution by a) decelerating the pendulum to 30% velocity if it exceeds 0.3 and b) forcibly changing
    the velocity to 0.3 if it exceeds 0.5
    */
    // if (this.a1_v >= 0.3) this.a1_v *= 0.3;
    // if (this.a2_v >= 0.3) this.a2_v *= 0.3;
    // if (this.a1_v >= 0.5) this.a1_v = 0.25;
    // if (this.a2_v >= 0.5) this.a2_v = 0.25;
  }

  this.show = function () {

    stroke(130);
    strokeWeight(1 * SCALE_LEN / 216);
    line(0, 0, this.x1 * SCALE_LEN, this.y1 * SCALE_LEN);
    line(this.x1 * SCALE_LEN, this.y1 * SCALE_LEN, this.x2 * SCALE_LEN, this.y2 * SCALE_LEN);
    fill(200);
    noStroke();
    ellipse(this.x1 * SCALE_LEN, this.y1 * SCALE_LEN, this.m1 * SCALE_MASS);
    ellipse(this.x2 * SCALE_LEN, this.y2 * SCALE_LEN, this.m2 * SCALE_MASS);
  }
}

function setup() {
  lineColors = [color(255, 0, 0), color(255, 127, 0), color(255, 255, 0),
  color(0, 255, 0), color(0, 0, 255), color(75, 0, 130), color(143, 0, 255)]; // holds the color values that each of the 7 pendulums should have

  createCanvas(WINDOW_SIZE[0], WINDOW_SIZE[1]);

  for (let i = 0; i < numPendulums; i++) {
    pendulums[i] = new Pendulum(i);
    traces[i] = new Line(pendulums[i].x2 * SCALE_LEN, pendulums[i].y2 * SCALE_LEN);
  }

  for (let i = 0; i < numPendulums; i++) {  // to fit every pendulum in the canvas, I scale the pendulums up or down based on the length of the longest rod
    lengthRod = pendulums[i].r1 + pendulums[i].r2;
    if (lengthRod > longestRod) longestRod = lengthRod; // this loop finds the longest rod for me
  }
  // the equations are in meters but p5 measures in pixels, so if I display a 1 meter long rod, it'll only be 1 pixel long. These scale factors make the rods and masses scale with the canvas size
  SCALE_LEN = 0.6 * height / longestRod;  // Ensures that the rods take up 60% of the window height (60% is arbitrarily chosen, I just thought it looked good)
  SCALE_MASS = SCALE_LEN / 21.6; // similar to SCALE_LEN but for the weights, not the rods (I also just thought 21.6 looked good)

  // Generates the .txt file that tells python what my starting parameters and offsets are
  let logParameters = createWriter('p5parameters.txt');
  logParameters.write(pendulums[0].compare(pendulums[1]));
  logParameters.close()
  print(pendulums[0].compare(pendulums[1]));

  //################################################################################  Make a button for CCapture.js that a user can press manually
  btn = document.createElement("button");
  btn.textContent = "start recording";
  document.body.appendChild(btn);
  btn.onclick = record;
  //################################################################################
}

function draw() {
  if (frameCount == 1 || frameCount == 901) btn.click(); // start recording CCapture.js automatically. 900 frames roughly corresponds to 15 seconds

  background(0);
  translate(width / 2, height * 0.35);  // puts the center of the pendulums in the middle horizontally and 35% down the screen vertically
  for (let i = 0; i < numPendulums; i++) {
    pendulums[i].update();
    traces[i].update(pendulums[i].x2 * SCALE_LEN, pendulums[i].y2 * SCALE_LEN);
  }
  for (let i = 0; i < numPendulums; i++) {
    traces[i].show(lineColors[i]);
  }
  for (let i = 0; i < numPendulums; i++) {   // These have to be in different for loops or else some traces will draw over some pendulums. I want all pendulums on top of all traces
    pendulums[i].show();
  }

  //################################################################################
  if (capturer) {
    capturer.capture(document.getElementById("defaultCanvas0"));  // Also for CCapture.js
  }
}
