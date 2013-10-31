#include <string>
#include <iostream>
#include <sstream>

int main () {
  double pi = 3.141592; // rough value

  std::string outputString;
  std::ostringstream outStr(outputString); // Output string stream 
 
  outStr.precision(5); // The default is 6.
  outStr << "pi=" << pi << ", "; // Append to string stream

  outStr << "sci pi=" << std::scientific << pi; // With scientific format

  std::cout << outStr.str() << std::endl; // Print the resulting string

  return 0;
}


