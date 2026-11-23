"""Exercise names and classifications checked against ACE's exercise library.

Instructions are original short cues, not copied exercise-library prose.
"""

ACE = "https://www.acefitness.org/resources/everyone/exercise-library/"
HKUST_FITNESS = "https://dst.hkust.edu.hk/support-%26-resources/sports-facilities/fitness-center"
CAMPUS_CENTERS = "HKUST LG4 Fitness Center / Tsang Shiu Tim Sports Center"
CAMPUS_GYM_EQUIPMENT = [
    ("Treadmill", "cardio", CAMPUS_CENTERS, HKUST_FITNESS),
    ("Bicycle ergometer", "cardio", CAMPUS_CENTERS, HKUST_FITNESS),
    ("Rowing ergometer", "cardio", CAMPUS_CENTERS, HKUST_FITNESS),
    ("Elliptical trainer", "cardio", CAMPUS_CENTERS, HKUST_FITNESS),
    ("Free weights", "strength", CAMPUS_CENTERS, HKUST_FITNESS),
    ("Multi-gym equipment", "strength", CAMPUS_CENTERS, HKUST_FITNESS),
]

# name, muscle group, equipment, difficulty, short cue, source
EXERCISES = [
    (
        "Seated row",
        "back",
        "machine",
        "beginner",
        "Sit tall; pull the handles toward your ribs, then return with control.",
        ACE + "168/seated-row/",
    ),
    (
        "Seated lat pulldown",
        "back",
        "machine",
        "beginner",
        "Pull toward the upper chest without swinging your torso; return slowly.",
        ACE + "158/seated-lat-pulldown/",
    ),
    (
        "Seated high back row",
        "back",
        "cable",
        "beginner",
        "Keep your chest lifted and draw elbows back without shrugging.",
        ACE + "46/seated-high-back-row/",
    ),
    (
        "Reverse fly",
        "back",
        "cable",
        "intermediate",
        "Use a light load and open the arms slowly while keeping your trunk steady.",
        ACE + "353/reverse-fly/",
    ),
    (
        "Seated machine close-grip shoulder press",
        "shoulders",
        "machine",
        "beginner",
        "Press smoothly overhead in a comfortable range; avoid arching your back.",
        ACE + "187/seated-machine-close-grip-shoulder-press/",
    ),
    (
        "Dumbbell shoulder press",
        "shoulders",
        "dumbbell",
        "intermediate",
        "Start light, brace your trunk and press overhead without forcing range.",
        "https://www.acefitness.org/resources/pros/expert-articles/5047/strength-training-workout-for-beginners/",
    ),
    (
        "Bent-arm lateral raise",
        "shoulders",
        "dumbbell",
        "intermediate",
        "Lift light dumbbells out to the sides to a comfortable height, then lower slowly.",
        "https://www.acefitness.org/resources/pros/expert-articles/9074/smart-shoulder-solutions-an-evidence-based-approach-to-training-the-deltoids/",
    ),
    (
        "Bent-knee push-up",
        "chest",
        "bodyweight",
        "beginner",
        "Keep a straight line from knees to head while lowering and pressing away.",
        ACE + "experience/beginner/",
    ),
    (
        "Dumbbell chest press",
        "chest",
        "dumbbell",
        "beginner",
        "Keep your shoulders settled and press the dumbbells upward with control.",
        "https://www.acefitness.org/resources/pros/expert-articles/5047/strength-training-workout-for-beginners/",
    ),
    (
        "Push-up",
        "chest",
        "bodyweight",
        "intermediate",
        "Brace your trunk, lower as one unit and press back up without sagging.",
        ACE + "41/push-up/",
    ),
    (
        "Bodyweight squat",
        "legs",
        "bodyweight",
        "beginner",
        "Sit hips back and down, keep heels grounded, then stand tall.",
        ACE + "135/bodyweight-squat/",
    ),
    (
        "Seated leg press",
        "legs",
        "machine",
        "beginner",
        "Press through your feet without locking the knees; return slowly.",
        ACE + "154/seated-leg-press/",
    ),
    (
        "Forward lunge",
        "legs",
        "bodyweight",
        "intermediate",
        "Step forward, lower with control and push back to standing.",
        ACE + "body-part/legs-thighs/",
    ),
    (
        "Cobra exercise",
        "core",
        "bodyweight",
        "beginner",
        "Lift the chest gently while keeping the movement comfortable and controlled.",
        ACE + "experience/beginner/",
    ),
    (
        "Crunch",
        "core",
        "bodyweight",
        "beginner",
        "Curl the upper trunk slightly without pulling on your neck.",
        ACE + "experience/beginner/",
    ),
    (
        "Bird-dog",
        "core",
        "bodyweight",
        "intermediate",
        "Extend opposite arm and leg while keeping your trunk steady.",
        ACE + "body-part/abs/",
    ),
    (
        "Dumbbell single-arm row", "back", "dumbbell", "beginner",
        "Brace on a stable bench and draw your elbow back without twisting your torso.",
        "https://www.acefitness.org/resources/pros/expert-articles/5047/strength-training-workout-for-beginners/",
    ),
    (
        "Seated incline cable press", "chest", "cable", "beginner",
        "Keep your back supported as you press the handles forward and up.",
        ACE + "167/seated-incline-cable-press/",
    ),
    (
        "Seated leg extension", "legs", "machine", "beginner",
        "Adjust the pad above the ankles; straighten and lower your legs smoothly.",
        ACE + "183/seated-leg-extension/",
    ),
    (
        "Dumbbell squat", "legs", "dumbbell", "intermediate",
        "Hold the dumbbells by your sides and lower into a comfortable squat.",
        "https://www.acefitness.org/resources/everyone/blog/5564/squat-variations-6-effective-squat-variations-to-try/",
    ),
    (
        "Glute bridge", "legs", "bodyweight", "beginner",
        "Press through your feet to lift your hips, then lower without arching your back.",
        ACE + "49/glute-bridge/",
    ),
    (
        "Side plank with bent knees", "core", "bodyweight", "beginner",
        "Support yourself on one forearm and your bent knees; keep your hips stacked.",
        "https://www.acefitness.org/resources/everyone/blog/6593/top-25-at-home-exercises/",
    ),
]

# Equipment needed for the movement, independent of campus inventory.
EQUIPMENT_DETAILS = {
    "Seated row": "Seated row machine",
    "Seated lat pulldown": "Lat pulldown station",
    "Seated high back row": "Low cable pulley and bench",
    "Reverse fly": "Dual cable station",
    "Seated machine close-grip shoulder press": "Shoulder press machine",
    "Dumbbell shoulder press": "Pair of dumbbells",
    "Bent-arm lateral raise": "Pair of dumbbells",
    "Dumbbell chest press": "Pair of dumbbells and flat bench",
    "Seated leg press": "Leg press machine",
    "Dumbbell single-arm row": "One dumbbell and stable bench",
    "Seated incline cable press": "Cable press station and incline seat",
    "Seated leg extension": "Leg extension machine",
    "Dumbbell squat": "Pair of dumbbells",
}
