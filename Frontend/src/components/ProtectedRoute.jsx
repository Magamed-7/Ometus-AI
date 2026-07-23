import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth/AuthContext.jsx";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center">
        <span className="material-symbols-outlined animate-spin text-primary">progress_activity</span>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;

  return children;
}
