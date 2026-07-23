import { Navigate } from "react-router-dom";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";

function RoleGate({ role, children }) {
  const { user } = useAuth();
  const allowed = Array.isArray(role) ? role.includes(user.role) : user.role === role;

  if (!allowed) return <Navigate to="/account" replace />;

  return children;
}

export default function RoleRoute({ role, children }) {
  return (
    <ProtectedRoute>
      <RoleGate role={role}>{children}</RoleGate>
    </ProtectedRoute>
  );
}
