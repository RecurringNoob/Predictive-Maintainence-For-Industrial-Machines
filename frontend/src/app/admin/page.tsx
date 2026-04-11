"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, Trash2 } from "lucide-react";
import { users as initialUsers, sensorMappings as initialSensorMappings, machines } from "@/lib/data";
import type { User, SensorMapping } from "@/lib/types";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function AdminPage() {
    const [users, setUsers] = useState<User[]>(initialUsers);
    const [sensorMappings, setSensorMappings] = useState<SensorMapping[]>(initialSensorMappings);

    const handleRoleChange = (email: string, role: User['role']) => {
        setUsers(users.map(u => u.email === email ? {...u, role} : u));
    }

    const handleAddSensor = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        const deviceId = formData.get('deviceId') as string;
        const machineId = formData.get('machineId') as string;
        if(deviceId && machineId) {
            const newMapping: SensorMapping = {
                id: `S-${String(sensorMappings.length + 1).padStart(3, '0')}`,
                deviceId,
                machineId,
            }
            setSensorMappings([newMapping, ...sensorMappings]);
            event.currentTarget.reset();
        }
    }

    const handleDeleteSensor = (id: string) => {
        setSensorMappings(sensorMappings.filter(sm => sm.id !== id));
    }

  return (
    <Tabs defaultValue="sensors">
      <div className="flex items-center">
        <TabsList>
          <TabsTrigger value="sensors">Sensor Registration</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
        </TabsList>
      </div>
      <TabsContent value="sensors" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Register New Sensor</CardTitle>
            <CardDescription>Map a new device ID to a machine ID.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid sm:grid-cols-3 gap-4" onSubmit={handleAddSensor}>
              <div className="grid gap-2">
                <Label htmlFor="deviceId">Device ID</Label>
                <Input id="deviceId" name="deviceId" placeholder="e.g., ESP32-A1B2C3" required />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="machineId">Machine ID</Label>
                <Select name="machineId" required>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a machine" />
                  </SelectTrigger>
                  <SelectContent>
                    {machines.map(m => <SelectItem key={m.id} value={m.id}>{m.id}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" className="self-end">Add Sensor</Button>
            </form>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Registered Sensors</CardTitle>
            <CardDescription>List of all registered sensor mappings.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Device ID</TableHead>
                  <TableHead>Machine ID</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sensorMappings.map(mapping => (
                    <TableRow key={mapping.id}>
                        <TableCell className="font-medium">{mapping.deviceId}</TableCell>
                        <TableCell>{mapping.machineId}</TableCell>
                        <TableCell>
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                <Button aria-haspopup="true" size="icon" variant="ghost">
                                    <MoreHorizontal className="h-4 w-4" />
                                    <span className="sr-only">Toggle menu</span>
                                </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                <DropdownMenuItem onClick={() => handleDeleteSensor(mapping.id)} className="text-destructive">
                                    <Trash2 className="mr-2 h-4 w-4" /> Delete
                                </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </TableCell>
                    </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="users">
        <Card>
          <CardHeader>
            <CardTitle>User Management</CardTitle>
            <CardDescription>Manage user roles and permissions.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.email}>
                    <TableCell>
                      <div className="flex items-center gap-4">
                        <Avatar className="hidden h-9 w-9 sm:flex">
                          <AvatarImage src={user.avatar} alt="Avatar" />
                          <AvatarFallback>{user.name.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div className="grid gap-1">
                          <p className="text-sm font-medium leading-none">{user.name}</p>
                          <p className="text-sm text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                        <Select value={user.role} onValueChange={(value: User['role']) => handleRoleChange(user.email, value)}>
                            <SelectTrigger className="w-[120px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="Admin">Admin</SelectItem>
                                <SelectItem value="Operator">Operator</SelectItem>
                                <SelectItem value="Viewer">Viewer</SelectItem>
                            </SelectContent>
                        </Select>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button aria-haspopup="true" size="icon" variant="ghost">
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">Toggle menu</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem>Edit</DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
