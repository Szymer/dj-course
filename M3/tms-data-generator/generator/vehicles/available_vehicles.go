package vehicles

import (
	"fmt"
	"strings"
	"time"
)

// AvailableVehicle reprezentuje dostępność pojazdu w danym dniu.
// Status: "available" - pojazd dostępny, "service" - dzień serwisowy.
type AvailableVehicle struct {
    ID            int
    VehicleID     int
    AvailableDate time.Time
    Status        string // "available", "service"
}

// GenerateAvailableVehicles generuje dostępność pojazdów na określoną liczbę dni.
// Co 10. dzień ustawia status "service".
func GenerateAvailableVehicles(vehicles []Vehicle, days int) []AvailableVehicle {
	var result []AvailableVehicle
	id := 1
	for _, v := range vehicles {
		for i := 0; i < days; i++ {
			date := time.Now().AddDate(0, 0, i)
			status := "available"
			// Przykładowa losowa logika na "service"
			if i%10 == 9 { // co 10 dzień serwis
				status = "service"
			}
			result = append(result, AvailableVehicle{
				ID:            id,
				VehicleID:     v.ID,
				AvailableDate: date,
				Status:        status,
			})
			id++
		}
	}
	return result
}

// GenerateAvailableVehiclesInsertStatements generuje polecenia INSERT dla dostępności pojazdów.
// Używa pola status typu string.
func GenerateAvailableVehiclesInsertStatements(avail []AvailableVehicle) string {
	var sb strings.Builder
	for _, a := range avail {
		sb.WriteString(fmt.Sprintf(
			"INSERT INTO available_vehicles (id, vehicle_id, available_date, status) VALUES (%d, %d, '%s', '%s');\n",
			a.ID, a.VehicleID, a.AvailableDate.Format("2006-01-02"), a.Status))
	}
	return sb.String()
}
