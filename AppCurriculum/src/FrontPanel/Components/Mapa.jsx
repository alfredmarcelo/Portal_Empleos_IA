import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './Styles/Apple_map.css';

// Ícono SVG estilizado para la vacante (Destino)
const iconDestino = L.divIcon({
    className: 'custom-job-pin',
    html: `
        <div style="
            position: relative;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="
                background: linear-gradient(135deg, #ef4444, #dc2626);
                width: 28px;
                height: 28px;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                border: 2px solid #ffffff;
                box-shadow: 0 4px 10px rgba(0,0,0,0.35);
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <span style="
                    transform: rotate(45deg);
                    font-size: 14px;
                    line-height: 1;
                ">💼</span>
            </div>
        </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 30],
    popupAnchor: [0, -30]
});

// Ícono SVG para la ubicación del usuario (Origen)
const iconUsuario = L.divIcon({
    className: 'custom-user-pin',
    html: `
        <div style="
            position: relative;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="
                position: absolute;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: rgba(37, 99, 235, 0.35);
            "></div>
            <div style="
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: #2563eb;
                border: 2.5px solid #ffffff;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            "></div>
        </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
});

function ControladorVista({ ruta, destino, position }) {
    const map = useMap();

    useEffect(() => {
        if (!map) return;

        // 1. Si hay ruta activa calculada, ajustar a la ruta
        if (ruta && ruta.length > 1) {
            try {
                const bounds = L.latLngBounds(ruta);
                map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
                return;
            } catch (e) {
                console.warn("Error al encuadrar ruta:", e);
            }
        }

        // 2. Si no hay ruta aún pero hay destino y posición válida
        const tienePosicion = position?.lat && position?.lng && (position.lat !== 0 || position.lng !== 0);
        if (destino?.lat && destino?.lng) {
            if (tienePosicion) {
                try {
                    const bounds = L.latLngBounds([
                        [position.lat, position.lng],
                        [destino.lat, destino.lng]
                    ]);
                    map.fitBounds(bounds, { padding: [35, 35], maxZoom: 15 });
                    return;
                } catch (e) {
                    console.warn("Error al encuadrar bounds:", e);
                }
            }
            // Centrar directo en el destino
            map.setView([destino.lat, destino.lng], 14);
        }
    }, [map, ruta, destino?.lat, destino?.lng, position?.lat, position?.lng]);

    return null;
}

export default function Mapa({ ruta = [], destino, position, style, parametros = true, puesto }) {
    const defaultCenter = [
        destino?.lat || position?.lat || 18.4861,
        destino?.lng || position?.lng || -69.9312
    ];

    const tienePosicionValida = position?.lat && position?.lng && (position.lat !== 0 || position.lng !== 0);
    const tieneDestinoValido = destino?.lat && destino?.lng && (destino.lat !== 0 || destino.lng !== 0);

    return (
        <MapContainer
            style={style}
            id="Maps"
            center={defaultCenter}
            zoom={13}
            {...(parametros === true ? {
                zoomControl: true,
                dragging: true,
                scrollWheelZoom: true,
                doubleClickZoom: true,
                touchZoom: true,
                boxZoom: true,
                keyboard: true,
                maxZoom: 18
            } : {})}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />

            {ruta && ruta.length > 0 && (
                <Polyline positions={ruta} color="#ef4444" weight={5} opacity={0.85} />
            )}

            <ControladorVista ruta={ruta} destino={destino} position={position} />

            {tieneDestinoValido && (
                <Marker position={[destino.lat, destino.lng]} icon={iconDestino}>
                    <Popup>
                        <div style={{ textAlign: 'center', minWidth: '130px' }}>
                            <strong style={{ color: '#111827', fontSize: '13px', display: 'block', marginBottom: '4px' }}>
                                {puesto || "Ubicación del Empleo"}
                            </strong>
                            <span style={{ fontSize: '11px', color: '#6b7280' }}>
                                GPS: {destino.lat.toFixed(4)}, {destino.lng.toFixed(4)}
                            </span>
                        </div>
                    </Popup>
                </Marker>
            )}

            {tienePosicionValida && (
                <Marker position={[position.lat, position.lng]} icon={iconUsuario}>
                    <Popup>
                        <div style={{ textAlign: 'center' }}>
                            <strong style={{ color: '#2563eb', fontSize: '12px' }}>Tu ubicación actual</strong>
                        </div>
                    </Popup>
                </Marker>
            )}
        </MapContainer>
    );
}