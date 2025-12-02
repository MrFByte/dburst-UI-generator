import { useDispatch } from "react-redux";
import { logout } from "@/core/redux/authSlice";
import { logoutUser } from "@/features/index/api/indexApi";
import { toast } from "@/shared/hooks/useToast";
import { useNavigate } from "react-router-dom";

export function useLogout() {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logoutUser();
      
      dispatch(logout());
      
      toast.success("Logged out successfully");
      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
      
      dispatch(logout());
      toast.error("Logout failed, but you've been signed out locally");
      navigate("/");
    }
  };

  return handleLogout;
}