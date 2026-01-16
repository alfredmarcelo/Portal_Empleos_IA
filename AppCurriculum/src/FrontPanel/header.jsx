import React from "react";
import "./Styles/header.css";
import { IoSunnyOutline } from "react-icons/io5";
import { HiSun } from "react-icons/hi";
import { useTheme } from "./ThemeContext";

export default function Header() {
  const { mode, toggleMode } = useTheme();

  return (
    <div id="Header">
      <div id="fantasma"></div>
      <div id="User-Account"></div>
      <div id="Modo_claro_oscuro">
        {mode === "dark" ? (
          <HiSun size={25} color="var(--icon-color)" onClick={toggleMode} />
        ) : (
          <IoSunnyOutline
            size={25}
            color="var(--icon-color)"
            onClick={toggleMode}
          />
        )}
      </div>
    </div>
  );
}
