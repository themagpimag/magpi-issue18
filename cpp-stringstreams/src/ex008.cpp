#include <sstream>
#include <iostream>
#include <string>

int strToLong(const std::string &inputString, long &l_value) {
  long longValue;
  std::istringstream inStr(inputString);
  inStr >> l_value;
  if ((inStr.rdstate() & std::ios_base::failbit) > 0) return 1;
  return 0;
}

int strToDouble(const std::string &inputString, double &d_value) {
  double doubleValue;
  std::istringstream inStr(inputString);
  inStr >> d_value;
  if ((inStr.rdstate() & std::ios_base::failbit) > 0) return 1;
  return 0;
}

int main() {
  std::string str = "1213333333333333222333";
  long l = 0;
  double d = 0.;
  int ret_val;
  if(strToLong(str,l) != 0) {
    std::cerr << "ERROR: strToLong failed!" << std::endl;
  }

  if(strToDouble(str,d) != 0) {
    std::cerr << "ERROR: strToDouble failed!" << std::endl;
  }
  
  std::cout << "l=" << l << ", d=" << d << std::endl;

  return 0;
}
