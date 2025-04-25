import React from "react";

function Benefits() {
  return (
    <>
      {/* Section 1 */}
      <section
        className="text-center py-10 font-title text-white"
        id="benefits"
      >
        <div>
          <h1 className="text-4xl font-bold text-red-600">
            Discover GymFluencer Benefits
          </h1>
          <p className="text-lg mt-10 mx-96">
            Unlock your full potential with GymFluencer your personal fitness
            partner for progress and motivation
          </p>
        </div>
        <div className="grid grid-cols-3">
          <div className="mt-28 mx-10">
            <h1 className="text-red-600 text-2xl mb-2">
              Effortless Workout Logging
            </h1>
            <p>
              Easily log your workouts and monitor your progress over time with
              our intuitive logging feature.
            </p>
            <div className="mt-32">
              <h1 className="text-red-600 text-2xl mb-2">
                Accurate Rep Counting
              </h1>
              <p>
                Count your reps accurately with our app, ensuring consistency
                and improved performance.
              </p>
            </div>
          </div>
          <div className="mt-10">
            <img src="/images/image.webp" alt="" />
          </div>
          <div className="mt-28 mx-10">
            <h1 className="text-red-600 text-2xl mb-2">
              Personalized Workout Plans
            </h1>
            <p>
              AI-powered workout plans tailored to your fitness level, goals,
              and progress.
            </p>
            <div className="mt-32">
              <h1 className="text-red-600 text-2xl mb-2">
                Personalized Diet Plans
              </h1>
              <p>
                Calculate calories burned during workouts and AI-customized meal
                plans for optimal nutrition and wellness{" "}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2 */}
      <section className="font-title">
        <div className="grid grid-cols-2 gap-6 mt-10 mb-10">
          <div className="flex flex-col mx-20 text-white">
            <h1 className="text-4xl font-bold text-red-600">
              ACHIEVE YOUR FITNESS GOALS
            </h1>
            <p className="text-lg mt-6">
              Custom workout plans designed to fit your specific needs and
              progress.
            </p>
            <p className="text-lg mt-6">
              Gain motivation and tips from professional coaches, available
              24/7.
            </p>
            <p className="text-lg mt-6">
              Monitor your progress with insightful analytics, set milestones,
              and celebrate your success.
            </p>
          </div>

          <div className="flex flex-col mx-20 text-white">
            <h1 className="text-4xl font-bold text-red-600">
              YOUR PERSONALIZED FITNESS HUB
            </h1>
            <p className="text-lg mt-6">
              Personalized workout routines tailored to your goals and
              preferences
            </p>
            <p className="text-lg mt-6">
              Get expert guidance with virtual coaching sessions, available
              anytime, anywhere.
            </p>
            <p className="text-lg mt-6">
              Track your fitness journey with detailed analytics, goal setting,
              and achievements.
            </p>
          </div>
        </div>
        <div className="overflow-hidden bg-red-500 py-3 text-white font-semibold">
          <p className="scrolling-text">
            PROGRESS TRACKING FITNESS PLANS . WORKOUT ROUTINES . PROGRESS
            TRACKING FITNESS PLANS . WORKOUT ROUTINES . PROGRESS TRACKING
            FITNESS PLANS . WORKOUT ROUTINES . PROGRESS TRACKING FITNESS PLANS .
            WORKOUT ROUTINES . PROGRESS TRACKING FITNESS PLANS . WORKOUT
            ROUTINES . PROGRESS TRACKING FITNESS PLANS . WORKOUT ROUTINES .
            PROGRESS TRACKING FITNESS PLANS . WORKOUT ROUTINES . PROGRESS
            TRACKING FITNESS PLANS . WORKOUT ROUTINES .
          </p>

          <style>
            {`
          @keyframes marquee {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
          }

          .scrolling-text {
            display: inline-block;
            white-space: nowrap;
            animation: marquee 40s linear infinite;
          }
        `}
          </style>
        </div>
      </section>
    </>
  );
}

export default Benefits;
