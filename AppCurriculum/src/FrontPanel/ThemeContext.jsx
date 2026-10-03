import React, { createContext, useContext, useState, useEffect } from "react";

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
    const [mode, setMode] = useState("dark");

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", mode);
    }, [mode]);

    const toggleMode = () => {
        setMode((prev) => (prev === "light" ? "dark" : "light"));
    };

    return (
        <ThemeContext.Provider value={{ mode, setMode, toggleMode }}>
            {children}
        </ThemeContext.Provider>
    );
}

// Hook interno para manejar tema local cuando no hay provider
function useLocalTheme() {
    const [mode, setMode] = useState("dark");

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", mode);
    }, [mode]);

    const toggleMode = () => {
        setMode((prev) => (prev === "light" ? "dark" : "light"));
    };

    return { mode, setMode, toggleMode };
}

export function useTheme() {
    const context = useContext(ThemeContext);
    const localTheme = useLocalTheme();

    // Si hay contexto, usarlo; si no, usar tema local
    return context || localTheme;
}
