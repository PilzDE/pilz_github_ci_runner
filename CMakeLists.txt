cmake_minimum_required(VERSION 3.0.2)
project(pilz_github_ci_runner)

find_package(catkin REQUIRED COMPONENTS
  roslint
  rospy
)

catkin_package()
catkin_python_setup()
catkin_install_python(PROGRAMS
    scripts/test_repository.py
    DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
