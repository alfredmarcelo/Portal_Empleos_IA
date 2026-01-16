import React from "react";
import { useTheme } from "../ThemeContext";
import "./Styles/LoadIndicator.css";

export default function LoadIndicator() {
    const { mode } = useTheme();
    return (
        <div>
            <div id="Load-Indicator">
                <div id="Load-Indicator-Container">
                    <div id="Load-Indicator-Container-Item"></div>
                    <div id="Load-Indicator-Container-Item"></div>
                    <div id="Load-Indicator-Container-Item"></div>
                </div>
                <div>
                    <text id="Load-Indicator-Text">Buscando</text>
                </div>
            </div>
        </div>
    )
}       