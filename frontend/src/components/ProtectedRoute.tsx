import { Navigate, Outlet } from 'react-router-dom';

export default function ProtectedRoute() {
    const token = localStorage.getItem('admin_token');

    // If there is no token, redirect to login page
    if (!token) {
        return <Navigate to="/login" replace />;
    }

    // Otherwise, render the child routes (Outlet)
    return <Outlet />;
}
