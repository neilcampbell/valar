import { Container } from "@/components/Container/Container";
import RoleSelector from "@/pages/Dashboard/_components/RoleSelector";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import useUserStore from "@/store/userStore";
import ValidatorDashboard from "./_components/ValidatorDashboard/ValidatorDashboard";
import DelegatorDashboard from "./_components/DelegatorDashboard/DelegatorDashboard";
import { ROLE_DEL_STR, ROLE_VAL_STR } from "@/constants/smart-contracts";
import { bytesToStr } from "@/utils/convert";

interface DashboardState {
  role?: string;
}

const Dashboard = () => {

  const { user } = useUserStore();
  const location = useLocation();
  const [ _role, setRole ] = useState<string | undefined>(undefined);

  //Get User Role
  useEffect(() => {
    const state = location.state as DashboardState | undefined;
    const role = state?.role;

    if(!role){
      if(user){
        if(user.userInfo){
          const role_fetched = bytesToStr(user.userInfo.role);
          if(role_fetched === ROLE_VAL_STR){
            setRole(ROLE_VAL_STR);
          }
          else if(role_fetched === ROLE_DEL_STR){
            setRole(ROLE_DEL_STR);
          }
          else{
            console.error("Unexpected user role: " + role_fetched);
            setRole(undefined);
          }
        } else {
          console.log("User not yet registered at the platform.");
          // Keep last selected role
        }
      } else {
        // Set to role that is passed during navigation
        setRole(role);
      }
    } else {
      // Set to role that is passed during navigation
      setRole(role);
    }
  }, [user, location]);

  // Display correct dashboard depending on user role
  if (_role === ROLE_VAL_STR) {
    return <ValidatorDashboard />
  }

  if (_role === ROLE_DEL_STR) {
    return <DelegatorDashboard />
  }

  // Default role selector for undefined role
  return (
    <Container>
      <RoleSelector setRole={setRole}/>
    </Container>
  );
};

export default Dashboard;
