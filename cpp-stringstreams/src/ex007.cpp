#include <string>
#include <sstream>
#include <iostream>

int main () {
  double d_value = 0.0;
  int i_value = 0;

  std::string str1("7.045 ");  // A space is needed
  std::string str2("12345 ");  // A space is needed

  // Very strange things happen if the trailing space is removed: the
  // next >> operation fails and no attempt to use seekg() or str()
  // will clear the problem.

  std::istringstream inStr(str1);

  // Collect a double value
  inStr >> d_value;

  // Reset the string to be re-read
  inStr.seekg(0);
  
  // Collect an int value
  inStr >> i_value;

  std::cout << "First String Stream:" << std::endl;
  std::cout << "d_value=" << d_value << std::endl;
  std::cout << "i_value=" << i_value << std::endl << std::endl;

  // Set the string value of the stream to the second string.
  inStr.str(str2);
  
  // Collect a double value
  inStr >> d_value;

  // Reset the string to be re-read
  inStr.seekg(0);

  // Collect an int value
  inStr >> i_value;

  std::cout << "Second String Stream:" << std::endl;
  std::cout << "d_value=" << d_value << std::endl;
  std::cout << "i_value=" << i_value << std::endl << std::endl;

  return 0;
}
