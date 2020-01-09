program compilefail39(output);
{enumerated type with more than 255 values}

type fruit = (apple, pear, banana, cherry,
	a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,
	a1,b1,c1,d1,e1,f1,g1,h1,i1,j1,k1,l1,m1,n1,o1,p1,q1,r1,s1,t1,u1,v1,w1,x1,y1,z1,
	a2,b2,c2,d2,e2,f2,g2,h2,i2,j2,k2,l2,m2,n2,o2,p2,q2,r2,s2,t2,u2,v2,w2,x2,y2,z2,
	a3,b3,c3,d3,e3,f3,g3,h3,i3,j3,k3,l3,m3,n3,o3,p3,q3,r3,s3,t3,u3,v3,w3,x3,y3,z3,
	aa1,ab1,ac1,ad1,ae1,af1,ag1,ah1,ai1,aj1,ak1,al1,am1,an1,ao1,ap1,aq1,ar1,as1,at1,au1,av1,aw1,ax1,ay1,az1,
	ba1,bb1,bc1,bd1,be1,bf1,bg1,bh1,bi1,bj1,bk1,bl1,bm1,bn1,bo1,bp1,bq1,br1,bs1,bt1,bu1,bv1,bw1,bx1,by1,bz1,
	ca1,cb1,cc1,cd1,ce1,cf1,cg1,ch1,ci1,cj1,ck1,cl1,cm1,cn1,co1,cp1,cq1,cr1,cs1,ct1,cu1,cv1,cw1,cx1,cy1,cz1,
	da1,db1,dc1,dd1,de1,df1,dg1,dh1,di1,dj1,dk1,dl1,dm1,dn1,do1,dp1,dq1,dr1,ds1,dt1,du1,dv1,dw1,dx1,dy1,dz1,
	ea1,eb1,ec1,ed1,ee1,ef1,eg1,eh1,ei1,ej1,ek1,el1,em1,en1,eo1,ep1,eq1,er1,es1,et1,eu1,ev1,ew1,ex1,ey1,ez1,
	fa1,fb1,fc1,fd1,fe1,ff1,fg1,fh1,fi1,fj1,fk1,fl1,fm1,fn1,fo1,fp1,fq1,fr1,fs1,ft1,fu1,fv1,fw1,fx1,fy1,fz1
);

var myfruit:fruit;

begin
	myfruit := cherry;
	writeln('it''s cherry');
	myfruit := pred(myfruit);
	writeln('now it''s banana');
	myfruit := pred(myfruit);
	writeln('now it''s pear');
	myfruit := pred(myfruit);
	writeln('now it''s apple');
	writeln('next line should fail with an error');
	myfruit := pred(myfruit);
	writeln('we shouldn''t get here.');

end.
