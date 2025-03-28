c     cut on the rapidity of the two leading leptons
      block
        integer :: mm, tmpvar

        j = 0 ! leading lepton index
        mm = 0 ! subleading lepton index
        do i=1,nexternal
          if (is_a_lm_reco(i) .or. is_a_lp_reco(i)) then
            tmpvar = pt_04(p(0,i))
            if (j.eq.0) then
              j = i
            else if (mm.eq.0) then
              if (tmpvar.ge.pt_04(p(0,j))) then
                mm = j
                j = i
              else if (tmpvar.ge.pt_04(p(0,mm))) then
                mm = i
              endif
            else if (tmpvar.ge.pt_04(p(0,j))) then
              mm = j
              j = i
            else if (tmpvar.ge.pt_04(p(0,mm))) then
              mm = i
            endif
          endif
        enddo
        if (abs(atanh((p(3,j)+p(3,mm))
     &      /(p(0,j)+p(0,mm)))) .gt. {}) then
          passcuts_leptons=.false.
          return
        endif
      end block
